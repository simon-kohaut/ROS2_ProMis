import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    package_dir = get_package_share_directory("promis_navigation")

    use_sim_time = LaunchConfiguration("use_sim_time")
    mission_config = LaunchConfiguration("mission_config")

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument(
                "mission_config",
                default_value=os.path.join(
                    package_dir,
                    "config",
                    "promis_mission_demo.yaml",
                ),
            ),
            Node(
                package="promis_runtime",
                executable="promis_map_node",
                name="promis_map_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "mission_config": mission_config,
                        "probability_grid_topic": "/promis/probability_grid",
                        "cost_grid_topic": "/promis/cost_grid",
                        "status_topic": "/promis/status",
                    }
                ],
            ),
        ]
    )
