"""Simple planar fake mobile base for RViz-only Nav2 validation."""

from __future__ import annotations

import math
from typing import Optional

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import TransformBroadcaster


class FakeBaseNode(Node):
    """Integrate `/cmd_vel` into `/odom` and `odom -> base_link` TF."""

    def __init__(self) -> None:
        super().__init__("fake_base_node")

        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("publish_rate_hz", 30.0)
        self.declare_parameter("cmd_vel_timeout_sec", 0.5)
        self.declare_parameter("initial_x", 0.0)
        self.declare_parameter("initial_y", 0.0)
        self.declare_parameter("initial_yaw", 0.0)

        self._cmd_vel_topic = str(self.get_parameter("cmd_vel_topic").value)
        self._odom_topic = str(self.get_parameter("odom_topic").value)
        self._odom_frame = str(self.get_parameter("odom_frame").value)
        self._base_frame = str(self.get_parameter("base_frame").value)
        self._cmd_vel_timeout_sec = float(
            self.get_parameter("cmd_vel_timeout_sec").value
        )

        self._x = float(self.get_parameter("initial_x").value)
        self._y = float(self.get_parameter("initial_y").value)
        self._yaw = float(self.get_parameter("initial_yaw").value)
        self._last_twist = Twist()
        self._last_cmd_time: Optional[Time] = None
        self._last_step_time: Optional[Time] = None

        self._odom_pub = self.create_publisher(Odometry, self._odom_topic, 10)
        self._tf_broadcaster = TransformBroadcaster(self)
        self._cmd_sub = self.create_subscription(
            Twist,
            self._cmd_vel_topic,
            self._on_cmd_vel,
            10,
        )

        rate = max(float(self.get_parameter("publish_rate_hz").value), 1.0)
        self._timer = self.create_timer(1.0 / rate, self._on_timer)

        self.get_logger().info(
            f"Fake base ready: cmd_vel={self._cmd_vel_topic}, odom={self._odom_topic}"
        )

    def _on_cmd_vel(self, msg: Twist) -> None:
        self._last_twist = msg
        self._last_cmd_time = self.get_clock().now()

    def _on_timer(self) -> None:
        now = self.get_clock().now()
        if self._last_step_time is None:
            self._last_step_time = now
            self._publish_state(now, Twist())
            return

        dt = (now - self._last_step_time).nanoseconds / 1_000_000_000.0
        self._last_step_time = now

        twist = self._current_twist(now)
        self._integrate(twist, dt)
        self._publish_state(now, twist)

    def _current_twist(self, now: Time) -> Twist:
        if self._last_cmd_time is None:
            return Twist()
        age = (now - self._last_cmd_time).nanoseconds / 1_000_000_000.0
        if age > self._cmd_vel_timeout_sec:
            return Twist()
        return self._last_twist

    def _integrate(self, twist: Twist, dt: float) -> None:
        vx = float(twist.linear.x)
        vy = float(twist.linear.y)
        wz = float(twist.angular.z)

        cos_yaw = math.cos(self._yaw)
        sin_yaw = math.sin(self._yaw)
        self._x += (vx * cos_yaw - vy * sin_yaw) * dt
        self._y += (vx * sin_yaw + vy * cos_yaw) * dt
        self._yaw = self._normalize_angle(self._yaw + wz * dt)

    def _publish_state(self, now: Time, twist: Twist) -> None:
        stamp = now.to_msg()
        qx, qy, qz, qw = self._quaternion_from_yaw(self._yaw)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self._odom_frame
        odom.child_frame_id = self._base_frame
        odom.pose.pose.position.x = self._x
        odom.pose.pose.position.y = self._y
        odom.pose.pose.orientation.x = qx
        odom.pose.pose.orientation.y = qy
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist = twist
        self._odom_pub.publish(odom)

        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = self._odom_frame
        transform.child_frame_id = self._base_frame
        transform.transform.translation.x = self._x
        transform.transform.translation.y = self._y
        transform.transform.translation.z = 0.0
        transform.transform.rotation.x = qx
        transform.transform.rotation.y = qy
        transform.transform.rotation.z = qz
        transform.transform.rotation.w = qw
        self._tf_broadcaster.sendTransform(transform)

    @staticmethod
    def _quaternion_from_yaw(yaw: float) -> tuple[float, float, float, float]:
        half = yaw / 2.0
        return (0.0, 0.0, math.sin(half), math.cos(half))

    @staticmethod
    def _normalize_angle(value: float) -> float:
        return math.atan2(math.sin(value), math.cos(value))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FakeBaseNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

