"""ROS node publishing real-time rolling ProMis probability and cost grids."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Optional, Tuple

import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from std_msgs.msg import String
from tf2_ros import Buffer, TransformException, TransformListener

from promis_runtime.mission_config import MissionConfig, load_mission_config
from promis_runtime.probability_cost import probabilities_to_occupancy
from promis_runtime.promis_engine import create_landscape_engine
from promis_runtime.rolling_window import cell_centers, make_grid_spec
from promis_runtime.ros_grid import make_occupancy_grid, probabilities_to_grid_data


Pose2D = Tuple[float, float, float]


class ProMisMapNode(Node):
    """Publish rolling probability and semantic cost grids for Nav2."""

    def __init__(self) -> None:
        super().__init__("promis_map_node")

        self.declare_parameter("mission_config", "")
        self.declare_parameter("probability_grid_topic", "/promis/probability_grid")
        self.declare_parameter("cost_grid_topic", "/promis/cost_grid")
        self.declare_parameter("status_topic", "/promis/status")

        mission_path = str(self.get_parameter("mission_config").value).strip()
        self._config = self._load_config(mission_path)
        self._engine = create_landscape_engine(self._config.engine)

        transient_qos = QoSProfile(depth=1)
        transient_qos.reliability = ReliabilityPolicy.RELIABLE
        transient_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        self._probability_pub = self.create_publisher(
            OccupancyGrid,
            str(self.get_parameter("probability_grid_topic").value),
            transient_qos,
        )
        self._cost_pub = self.create_publisher(
            OccupancyGrid,
            str(self.get_parameter("cost_grid_topic").value),
            transient_qos,
        )
        self._status_pub = self.create_publisher(
            String,
            str(self.get_parameter("status_topic").value),
            10,
        )

        self._tf_buffer = Buffer(cache_time=Duration(seconds=10.0))
        self._tf_listener = TransformListener(self._tf_buffer, self)
        self._last_pose: Optional[Pose2D] = None
        self._last_publish_monotonic: Optional[float] = None

        update_rate = max(self._config.runtime.update_rate_hz, 0.01)
        self._timer = self.create_timer(1.0 / update_rate, self._on_timer)

        self.get_logger().info(
            "ProMis map node ready: "
            f"engine={self._engine.name}, "
            f"global_frame={self._config.runtime.global_frame}, "
            f"robot_frame={self._config.runtime.robot_frame}"
        )

    def _load_config(self, mission_path: str) -> MissionConfig:
        if mission_path:
            path = Path(mission_path).expanduser()
            self.get_logger().info(f"Loading mission config: {path}")
            return load_mission_config(path)
        self.get_logger().warn("No mission_config parameter set; using default demo config")
        return MissionConfig()

    def _on_timer(self) -> None:
        try:
            pose = self._lookup_robot_pose()
        except TransformException as exc:
            self._publish_status(event="tf_unavailable", error=str(exc))
            return

        if not self._should_recompute(pose):
            return

        started = time.monotonic()
        spec = make_grid_spec(pose[0], pose[1], self._config.rolling_window)
        coordinates = cell_centers(spec)

        try:
            probabilities = self._engine.evaluate(coordinates)
        except Exception as exc:
            self.get_logger().error(f"Failed to evaluate ProMis landscape: {exc}")
            self._publish_status(event="engine_error", error=str(exc))
            return

        stamp = self.get_clock().now().to_msg()
        probability_grid = make_occupancy_grid(
            frame_id=self._config.runtime.global_frame,
            stamp=stamp,
            spec=spec,
            data=probabilities_to_grid_data(probabilities),
        )
        cost_grid = make_occupancy_grid(
            frame_id=self._config.runtime.global_frame,
            stamp=stamp,
            spec=spec,
            data=probabilities_to_occupancy(
                probabilities,
                self._config.cost_conversion,
            ),
        )

        self._probability_pub.publish(probability_grid)
        self._cost_pub.publish(cost_grid)
        self._last_pose = pose
        self._last_publish_monotonic = time.monotonic()

        self._publish_status(
            event="grid_published",
            engine=self._engine.name,
            width=spec.width_cells,
            height=spec.height_cells,
            resolution=spec.resolution_m,
            origin_x=round(spec.origin_x, 3),
            origin_y=round(spec.origin_y, 3),
            robot_x=round(pose[0], 3),
            robot_y=round(pose[1], 3),
            duration_sec=round(time.monotonic() - started, 3),
        )

    def _lookup_robot_pose(self) -> Pose2D:
        transform = self._tf_buffer.lookup_transform(
            self._config.runtime.global_frame,
            self._config.runtime.robot_frame,
            Time(),
        )
        translation = transform.transform.translation
        rotation = transform.transform.rotation
        return (
            float(translation.x),
            float(translation.y),
            self._yaw_from_quaternion(rotation.x, rotation.y, rotation.z, rotation.w),
        )

    def _should_recompute(self, pose: Pose2D) -> bool:
        if self._last_pose is None:
            return True

        dx = pose[0] - self._last_pose[0]
        dy = pose[1] - self._last_pose[1]
        dtheta = abs(self._angle_delta(pose[2], self._last_pose[2]))
        moved = math.hypot(dx, dy) >= self._config.runtime.min_recompute_translation_m
        turned = dtheta >= self._config.runtime.min_recompute_yaw_rad

        stale = False
        if self._last_publish_monotonic is not None:
            stale = (
                time.monotonic() - self._last_publish_monotonic
                >= self._config.runtime.stale_timeout_sec
            )

        return moved or turned or stale

    def _publish_status(self, **payload) -> None:
        msg = String()
        msg.data = json.dumps(payload, sort_keys=True)
        self._status_pub.publish(msg)

    @staticmethod
    def _angle_delta(a: float, b: float) -> float:
        return math.atan2(math.sin(a - b), math.cos(a - b))

    @staticmethod
    def _yaw_from_quaternion(x: float, y: float, z: float, w: float) -> float:
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        return math.atan2(siny_cosp, cosy_cosp)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ProMisMapNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
