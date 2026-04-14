"""Small Python bridge from a PoseStamped topic to Nav2 NavigateToPose."""

from __future__ import annotations

import json
from typing import Dict, Optional

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.task import Future
from std_msgs.msg import Empty, String


GOAL_STATUS_LABELS: Dict[int, str] = {
    GoalStatus.STATUS_UNKNOWN: "unknown",
    GoalStatus.STATUS_ACCEPTED: "accepted",
    GoalStatus.STATUS_EXECUTING: "executing",
    GoalStatus.STATUS_CANCELING: "canceling",
    GoalStatus.STATUS_SUCCEEDED: "succeeded",
    GoalStatus.STATUS_CANCELED: "canceled",
    GoalStatus.STATUS_ABORTED: "aborted",
}


class Nav2GoalBridge(Node):
    """Forward `/platform/goal_pose` to Nav2's NavigateToPose action."""

    def __init__(self) -> None:
        super().__init__("nav2_goal_bridge")

        self.declare_parameter("goal_topic", "/platform/goal_pose")
        self.declare_parameter("cancel_topic", "/platform/cancel_navigation")
        self.declare_parameter("status_topic", "/platform/navigation_status")
        self.declare_parameter("feedback_topic", "/platform/navigation_feedback")
        self.declare_parameter("action_name", "/navigate_to_pose")
        self.declare_parameter("wait_for_server_sec", 1.0)

        self._goal_topic = str(self.get_parameter("goal_topic").value)
        self._cancel_topic = str(self.get_parameter("cancel_topic").value)
        self._status_topic = str(self.get_parameter("status_topic").value)
        self._feedback_topic = str(self.get_parameter("feedback_topic").value)
        self._action_name = str(self.get_parameter("action_name").value)
        self._wait_for_server_sec = float(
            self.get_parameter("wait_for_server_sec").value
        )

        self._status_pub = self.create_publisher(String, self._status_topic, 10)
        self._feedback_pub = self.create_publisher(String, self._feedback_topic, 10)
        self._goal_sub = self.create_subscription(
            PoseStamped,
            self._goal_topic,
            self._on_goal,
            10,
        )
        self._cancel_sub = self.create_subscription(
            Empty,
            self._cancel_topic,
            self._on_cancel,
            10,
        )
        self._action_client = ActionClient(self, NavigateToPose, self._action_name)
        self._active_goal_handle = None

    def _on_goal(self, pose: PoseStamped) -> None:
        if not self._action_client.wait_for_server(timeout_sec=self._wait_for_server_sec):
            self._publish_status(event="server_unavailable", action_name=self._action_name)
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose
        self._publish_status(
            event="goal_received",
            frame_id=pose.header.frame_id,
            x=round(float(pose.pose.position.x), 3),
            y=round(float(pose.pose.position.y), 3),
        )

        future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self._on_feedback,
        )
        future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future: Future) -> None:
        try:
            goal_handle = future.result()
        except Exception as exc:
            self._publish_status(event="goal_send_failed", error=str(exc))
            return

        if goal_handle is None or not goal_handle.accepted:
            self._publish_status(event="goal_rejected")
            return

        self._active_goal_handle = goal_handle
        self._publish_status(event="goal_accepted")
        goal_handle.get_result_async().add_done_callback(self._on_result)

    def _on_result(self, future: Future) -> None:
        try:
            result = future.result()
        except Exception as exc:
            self._publish_status(event="goal_result_failed", error=str(exc))
            return

        self._publish_status(
            event="goal_finished",
            status=GOAL_STATUS_LABELS.get(result.status, "unknown"),
            status_code=result.status,
        )
        self._active_goal_handle = None

    def _on_feedback(self, feedback_msg) -> None:
        feedback = feedback_msg.feedback
        msg = String()
        msg.data = json.dumps(
            {
                "event": "feedback",
                "distance_remaining": round(float(feedback.distance_remaining), 3),
                "estimated_time_remaining_sec": self._duration_to_seconds(
                    feedback.estimated_time_remaining
                ),
                "navigation_time_sec": self._duration_to_seconds(
                    feedback.navigation_time
                ),
                "number_of_recoveries": int(feedback.number_of_recoveries),
            },
            sort_keys=True,
        )
        self._feedback_pub.publish(msg)

    def _on_cancel(self, _: Empty) -> None:
        if self._active_goal_handle is None:
            self._publish_status(event="cancel_ignored", reason="no_active_goal")
            return
        self._active_goal_handle.cancel_goal_async().add_done_callback(
            self._on_cancel_response
        )

    def _on_cancel_response(self, future: Future) -> None:
        try:
            response = future.result()
        except Exception as exc:
            self._publish_status(event="cancel_failed", error=str(exc))
            return
        self._publish_status(
            event="cancel_response",
            accepted=bool(response.goals_canceling),
        )

    def _publish_status(self, **payload) -> None:
        msg = String()
        msg.data = json.dumps(payload, sort_keys=True)
        self._status_pub.publish(msg)

    @staticmethod
    def _duration_to_seconds(duration_msg) -> Optional[float]:
        if duration_msg is None:
            return None
        return round(duration_msg.sec + duration_msg.nanosec / 1_000_000_000.0, 3)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = Nav2GoalBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

