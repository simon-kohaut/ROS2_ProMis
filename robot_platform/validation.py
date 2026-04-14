import argparse
import json
import math
from dataclasses import dataclass
from typing import Sequence


def probability_to_cost(probability: float) -> int:
    if math.isnan(probability):
        probability = 0.0
    probability = min(max(probability, 0.0), 1.0)
    return int(round(254.0 * (1.0 - probability)))


def cost_to_pgm_pixel(cost: int) -> int:
    cost = min(max(int(cost), 0), 254)
    return 255 - cost


@dataclass(frozen=True)
class PathSummary:
    pose_count: int
    path_length_m: float
    average_y: float
    min_y: float
    max_y: float
    corridor: str

    def as_dict(self) -> dict:
        return {
            "pose_count": self.pose_count,
            "path_length_m": self.path_length_m,
            "average_y": self.average_y,
            "min_y": self.min_y,
            "max_y": self.max_y,
            "corridor": self.corridor,
        }


def infer_corridor(y_values: Sequence[float], split_y: float = 0.0) -> str:
    if not y_values:
        raise ValueError("Cannot infer a corridor from an empty path")
    average_y = sum(y_values) / len(y_values)
    return "top" if average_y >= split_y else "bottom"


def summarize_path(path, split_y: float = 0.0) -> PathSummary:
    if not path.poses:
        raise ValueError("Planner returned an empty path")

    y_values = [float(p.pose.position.y) for p in path.poses]
    total_length = 0.0
    previous = None
    for pose in path.poses:
        current = pose.pose.position
        if previous is not None:
            dx = float(current.x) - float(previous.x)
            dy = float(current.y) - float(previous.y)
            total_length += math.hypot(dx, dy)
        previous = current

    return PathSummary(
        pose_count=len(path.poses),
        path_length_m=round(total_length, 3),
        average_y=round(sum(y_values) / len(y_values), 3),
        min_y=round(min(y_values), 3),
        max_y=round(max(y_values), 3),
        corridor=infer_corridor(y_values, split_y=split_y),
    )


def _build_pose(frame_id: str, x: float, y: float):
    from geometry_msgs.msg import PoseStamped

    msg = PoseStamped()
    msg.header.frame_id = frame_id
    msg.pose.position.x = float(x)
    msg.pose.position.y = float(y)
    msg.pose.position.z = 0.0
    msg.pose.orientation.w = 1.0
    return msg


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send a ComputePathToPose request and summarize which corridor the path uses."
    )
    parser.add_argument(
        "--action-name",
        default="/compute_path_to_pose",
        help="ComputePathToPose action name",
    )
    parser.add_argument("--frame-id", default="map", help="Frame id for start and goal")
    parser.add_argument("--start-x", type=float, default=-9.0)
    parser.add_argument("--start-y", type=float, default=0.0)
    parser.add_argument("--goal-x", type=float, default=9.0)
    parser.add_argument("--goal-y", type=float, default=0.0)
    parser.add_argument(
        "--expected-corridor",
        choices=["top", "bottom"],
        help="Fail if the resulting path does not prefer this corridor",
    )
    parser.add_argument(
        "--split-y",
        type=float,
        default=0.0,
        help="Y threshold used to decide whether a path belongs to the top or bottom corridor",
    )
    parser.add_argument(
        "--planner-id",
        default="GridBased",
        help="Optional planner id passed to ComputePathToPose",
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=20.0,
        help="How long to wait for the action server and result",
    )
    return parser


def main(args=None) -> int:
    import rclpy
    from action_msgs.msg import GoalStatus
    from nav2_msgs.action import ComputePathToPose
    from rclpy.action import ActionClient
    from rclpy.node import Node

    parsed = build_arg_parser().parse_args(args=args)

    class PathProbeNode(Node):
        def __init__(self, action_name: str) -> None:
            super().__init__("validate_nav2_path")
            self._client = ActionClient(self, ComputePathToPose, action_name)

        def compute_path(
            self,
            *,
            frame_id: str,
            start_xy: tuple[float, float],
            goal_xy: tuple[float, float],
            planner_id: str,
            timeout_sec: float,
        ):
            if not self._client.wait_for_server(timeout_sec=timeout_sec):
                raise RuntimeError("ComputePathToPose action server is unavailable")

            goal = ComputePathToPose.Goal()
            goal.use_start = True
            goal.planner_id = planner_id
            goal.start = _build_pose(frame_id, start_xy[0], start_xy[1])
            goal.goal = _build_pose(frame_id, goal_xy[0], goal_xy[1])

            send_goal_future = self._client.send_goal_async(goal)
            goal_handle = self._await_future(send_goal_future, timeout_sec)
            if goal_handle is None or not goal_handle.accepted:
                raise RuntimeError("ComputePathToPose goal was rejected")

            result_future = goal_handle.get_result_async()
            result = self._await_future(result_future, timeout_sec)
            if result is None:
                raise RuntimeError(
                    "Timed out while waiting for ComputePathToPose result"
                )
            if result.status != GoalStatus.STATUS_SUCCEEDED:
                raise RuntimeError(
                    f"ComputePathToPose returned status code {result.status}"
                )

            return result.result.path

        def _await_future(self, future, timeout_sec: float):
            rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_sec)
            if not future.done():
                return None
            return future.result()

    rclpy.init()
    node = PathProbeNode(parsed.action_name)
    exit_code = 0
    try:
        path = node.compute_path(
            frame_id=parsed.frame_id,
            start_xy=(parsed.start_x, parsed.start_y),
            goal_xy=(parsed.goal_x, parsed.goal_y),
            planner_id=parsed.planner_id,
            timeout_sec=parsed.timeout_sec,
        )
        summary = summarize_path(path, split_y=parsed.split_y)
        if parsed.expected_corridor and summary.corridor != parsed.expected_corridor:
            exit_code = 1
        print(json.dumps(summary.as_dict(), sort_keys=True))
    finally:
        node.destroy_node()
        rclpy.shutdown()

    raise SystemExit(exit_code)
