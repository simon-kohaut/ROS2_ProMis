from robot_platform.adapters.base import RobotAdapter
from robot_platform.models import TopicMap


class GenericMobileBaseAdapter(RobotAdapter):
    robot_type = "generic_mobile_base"

    def default_topics(self) -> TopicMap:
        return TopicMap(cmd_vel="/cmd_vel", odom="/odom", scan="/scan")
