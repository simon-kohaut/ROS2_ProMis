from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class TopicMap:
    cmd_vel: str
    odom: str
    scan: Optional[str]


@dataclass(frozen=True)
class FrameMap:
    global_frame: str
    odom_frame: str
    base_frame: str


@dataclass(frozen=True)
class AdapterConfig:
    robot_name: str
    robot_type: str
    topics: TopicMap
    frames: FrameMap
    supports_navigation: bool = True

    def as_dict(self) -> Dict[str, object]:
        return {
            "robot_name": self.robot_name,
            "robot_type": self.robot_type,
            "supports_navigation": self.supports_navigation,
            "topics": {
                "cmd_vel": self.topics.cmd_vel,
                "odom": self.topics.odom,
                "scan": self.topics.scan,
            },
            "frames": {
                "global_frame": self.frames.global_frame,
                "odom_frame": self.frames.odom_frame,
                "base_frame": self.frames.base_frame,
            },
        }
