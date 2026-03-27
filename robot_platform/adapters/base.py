from abc import ABC, abstractmethod
from typing import Mapping, Optional

from robot_platform.models import AdapterConfig, FrameMap, TopicMap


class RobotAdapter(ABC):
    robot_type = "base"

    @abstractmethod
    def default_topics(self) -> TopicMap:
        raise NotImplementedError

    def default_frames(self) -> FrameMap:
        return FrameMap(global_frame="map", odom_frame="odom", base_frame="base_link")

    def supports_navigation(self) -> bool:
        return True

    def build_config(
        self,
        robot_name: str,
        overrides: Mapping[str, Optional[str]],
        enable_scan: bool = True,
    ) -> AdapterConfig:
        topics = self.default_topics()
        frames = self.default_frames()

        cmd_vel_topic = overrides.get("cmd_vel_topic") or topics.cmd_vel
        odom_topic = overrides.get("odom_topic") or topics.odom
        scan_topic = topics.scan if enable_scan else None
        if enable_scan and overrides.get("scan_topic"):
            scan_topic = overrides["scan_topic"]

        global_frame = overrides.get("global_frame") or frames.global_frame
        odom_frame = overrides.get("odom_frame") or frames.odom_frame
        base_frame = overrides.get("base_frame") or frames.base_frame

        return AdapterConfig(
            robot_name=robot_name,
            robot_type=self.robot_type,
            topics=TopicMap(
                cmd_vel=cmd_vel_topic,
                odom=odom_topic,
                scan=scan_topic,
            ),
            frames=FrameMap(
                global_frame=global_frame,
                odom_frame=odom_frame,
                base_frame=base_frame,
            ),
            supports_navigation=self.supports_navigation(),
        )
