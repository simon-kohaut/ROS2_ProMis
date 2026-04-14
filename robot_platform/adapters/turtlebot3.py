from robot_platform.adapters.base import RobotAdapter
from robot_platform.models import FrameMap, TopicMap


class TurtleBot3Adapter(RobotAdapter):
    robot_type = "turtlebot3"

    def default_topics(self) -> TopicMap:
        return TopicMap(cmd_vel="/cmd_vel", odom="/odom", scan="/scan")

    def default_frames(self) -> FrameMap:
        return FrameMap(global_frame="map", odom_frame="odom", base_frame="base_link")
