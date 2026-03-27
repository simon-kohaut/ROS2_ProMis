import json
from typing import Optional

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String

from robot_platform.registry import create_adapter


class PlatformRouterNode(Node):
    def __init__(self) -> None:
        super().__init__("platform_router")

        self.declare_parameter("robot_name", "robot")
        self.declare_parameter("robot_type", "generic_mobile_base")
        self.declare_parameter("enable_scan", True)
        self.declare_parameter("cmd_vel_topic", "")
        self.declare_parameter("odom_topic", "")
        self.declare_parameter("scan_topic", "")
        self.declare_parameter("global_frame", "")
        self.declare_parameter("odom_frame", "")
        self.declare_parameter("base_frame", "")
        self.declare_parameter("platform_cmd_vel_topic", "/platform/cmd_vel")
        self.declare_parameter("platform_odom_topic", "/platform/odom")
        self.declare_parameter("platform_scan_topic", "/platform/scan")
        self.declare_parameter("platform_status_topic", "/platform/status")
        self.declare_parameter("status_period_sec", 1.0)

        robot_name = str(self.get_parameter("robot_name").value)
        robot_type = str(self.get_parameter("robot_type").value)
        enable_scan = bool(self.get_parameter("enable_scan").value)

        overrides = {
            "cmd_vel_topic": self._read_optional_string("cmd_vel_topic"),
            "odom_topic": self._read_optional_string("odom_topic"),
            "scan_topic": self._read_optional_string("scan_topic"),
            "global_frame": self._read_optional_string("global_frame"),
            "odom_frame": self._read_optional_string("odom_frame"),
            "base_frame": self._read_optional_string("base_frame"),
        }

        self._config = create_adapter(robot_type).build_config(
            robot_name=robot_name,
            overrides=overrides,
            enable_scan=enable_scan,
        )

        platform_cmd_vel_topic = str(self.get_parameter("platform_cmd_vel_topic").value)
        platform_odom_topic = str(self.get_parameter("platform_odom_topic").value)
        platform_scan_topic = str(self.get_parameter("platform_scan_topic").value)
        platform_status_topic = str(self.get_parameter("platform_status_topic").value)
        status_period_sec = float(self.get_parameter("status_period_sec").value)

        self._robot_cmd_vel_pub = self.create_publisher(
            Twist, self._config.topics.cmd_vel, 10
        )
        self._platform_odom_pub = self.create_publisher(
            Odometry, platform_odom_topic, 10
        )
        self._platform_scan_pub = None
        if self._config.topics.scan:
            self._platform_scan_pub = self.create_publisher(
                LaserScan, platform_scan_topic, qos_profile_sensor_data
            )

        self._status_pub = self.create_publisher(String, platform_status_topic, 10)

        self._platform_cmd_vel_sub = self.create_subscription(
            Twist, platform_cmd_vel_topic, self._on_platform_cmd_vel, 10
        )
        self._robot_odom_sub = self.create_subscription(
            Odometry, self._config.topics.odom, self._on_robot_odom, 10
        )
        self._robot_scan_sub = None
        if self._config.topics.scan:
            self._robot_scan_sub = self.create_subscription(
                LaserScan,
                self._config.topics.scan,
                self._on_robot_scan,
                qos_profile_sensor_data,
            )

        self._last_cmd_vel_time: Optional[Time] = None
        self._last_odom_time: Optional[Time] = None
        self._last_scan_time: Optional[Time] = None

        self._status_timer = self.create_timer(status_period_sec, self._publish_status)

        self.get_logger().info(
            f"Platform router ready: {json.dumps(self._config.as_dict(), sort_keys=True)}"
        )

    def _read_optional_string(self, parameter_name: str) -> Optional[str]:
        value = str(self.get_parameter(parameter_name).value).strip()
        return value or None

    def _on_platform_cmd_vel(self, msg: Twist) -> None:
        self._last_cmd_vel_time = self.get_clock().now()
        self._robot_cmd_vel_pub.publish(msg)

    def _on_robot_odom(self, msg: Odometry) -> None:
        self._last_odom_time = self.get_clock().now()
        self._platform_odom_pub.publish(msg)

    def _on_robot_scan(self, msg: LaserScan) -> None:
        self._last_scan_time = self.get_clock().now()
        if self._platform_scan_pub is not None:
            self._platform_scan_pub.publish(msg)

    def _publish_status(self) -> None:
        payload = self._config.as_dict()
        payload["ages_sec"] = {
            "cmd_vel": self._age_seconds(self._last_cmd_vel_time),
            "odom": self._age_seconds(self._last_odom_time),
            "scan": self._age_seconds(self._last_scan_time),
        }
        payload["healthy"] = self._last_odom_time is not None

        msg = String()
        msg.data = json.dumps(payload, sort_keys=True)
        self._status_pub.publish(msg)

    def _age_seconds(self, last_time: Optional[Time]) -> Optional[float]:
        if last_time is None:
            return None
        delta = self.get_clock().now() - last_time
        return round(delta.nanoseconds / 1_000_000_000.0, 3)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = PlatformRouterNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
