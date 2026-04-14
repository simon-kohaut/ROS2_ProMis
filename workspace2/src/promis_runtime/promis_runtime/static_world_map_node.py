"""Publish a simple static free-space map for RViz/Nav2 simulation."""

from __future__ import annotations

import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy


class StaticWorldMapNode(Node):
    """Publish an all-free OccupancyGrid on `/map`."""

    def __init__(self) -> None:
        super().__init__("static_world_map_node")

        self.declare_parameter("map_topic", "/map")
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("width_m", 60.0)
        self.declare_parameter("height_m", 60.0)
        self.declare_parameter("resolution_m", 0.1)
        self.declare_parameter("publish_period_sec", 2.0)

        qos = QoSProfile(depth=1)
        qos.reliability = ReliabilityPolicy.RELIABLE
        qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        self._map_topic = str(self.get_parameter("map_topic").value)
        self._frame_id = str(self.get_parameter("frame_id").value)
        self._width_m = float(self.get_parameter("width_m").value)
        self._height_m = float(self.get_parameter("height_m").value)
        self._resolution_m = float(self.get_parameter("resolution_m").value)

        self._pub = self.create_publisher(OccupancyGrid, self._map_topic, qos)
        self._timer = self.create_timer(
            max(float(self.get_parameter("publish_period_sec").value), 0.1),
            self._publish_map,
        )
        self._publish_map()

        self.get_logger().info(
            f"Static world map publishing: topic={self._map_topic}, "
            f"size={self._width_m}x{self._height_m}m"
        )

    def _publish_map(self) -> None:
        width_cells = max(1, int(round(self._width_m / self._resolution_m)))
        height_cells = max(1, int(round(self._height_m / self._resolution_m)))

        grid = OccupancyGrid()
        grid.header.stamp = self.get_clock().now().to_msg()
        grid.header.frame_id = self._frame_id
        grid.info.map_load_time = grid.header.stamp
        grid.info.resolution = self._resolution_m
        grid.info.width = width_cells
        grid.info.height = height_cells
        grid.info.origin.position.x = -0.5 * width_cells * self._resolution_m
        grid.info.origin.position.y = -0.5 * height_cells * self._resolution_m
        grid.info.origin.orientation.w = 1.0
        grid.data = [0] * (width_cells * height_cells)
        self._pub.publish(grid)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = StaticWorldMapNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

