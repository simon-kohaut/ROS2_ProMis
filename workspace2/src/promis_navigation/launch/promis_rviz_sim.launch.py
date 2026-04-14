import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    package_dir = get_package_share_directory("promis_navigation")

    use_sim_time = LaunchConfiguration("use_sim_time")
    autostart = LaunchConfiguration("autostart")
    mission_mode = LaunchConfiguration("mission_mode")
    params_file = LaunchConfiguration("params_file")
    mission_config = LaunchConfiguration("mission_config")
    rviz_config = LaunchConfiguration("rviz_config")
    use_rviz = LaunchConfiguration("use_rviz")
    use_goal_bridge = LaunchConfiguration("use_goal_bridge")
    log_level = LaunchConfiguration("log_level")
    default_mission_config = [
        TextSubstitution(text=os.path.join(package_dir, "config", "promis_mission_")),
        mission_mode,
        TextSubstitution(text=".yaml"),
    ]

    fake_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_dir, "launch", "include", "fake_base.launch.py")
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    promis_runtime_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_dir, "launch", "include", "promis_runtime.launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "mission_config": mission_config,
        }.items(),
    )

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_dir, "launch", "include", "navigation_base.launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "autostart": autostart,
            "params_file": params_file,
            "log_level": log_level,
        }.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("autostart", default_value="true"),
            DeclareLaunchArgument("use_rviz", default_value="true"),
            DeclareLaunchArgument("use_goal_bridge", default_value="true"),
            DeclareLaunchArgument("log_level", default_value="info"),
            DeclareLaunchArgument(
                "mission_mode",
                default_value="demo",
                choices=["demo", "promis"],
                description=(
                    "Select the built-in mission config profile. Use 'demo' for "
                    "the deterministic RViz simulation engine, or 'promis' for "
                    "the real ProMis adapter config."
                ),
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=os.path.join(
                    package_dir,
                    "config",
                    "nav2_promis_python_only.yaml",
                ),
            ),
            DeclareLaunchArgument(
                "mission_config",
                default_value=default_mission_config,
                description=(
                    "Path to a mission YAML file. If omitted, this is derived "
                    "from mission_mode."
                ),
            ),
            DeclareLaunchArgument(
                "rviz_config",
                default_value=os.path.join(
                    package_dir,
                    "rviz",
                    "promis_navigation.rviz",
                ),
            ),
            fake_base_launch,
            promis_runtime_launch,
            TimerAction(period=1.0, actions=[nav2_launch]),
            Node(
                condition=IfCondition(use_goal_bridge),
                package="promis_runtime",
                executable="nav2_goal_bridge",
                name="rviz_goal_bridge",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "goal_topic": "/goal_pose",
                        "cancel_topic": "/platform/cancel_navigation",
                        "status_topic": "/platform/navigation_status",
                        "feedback_topic": "/platform/navigation_feedback",
                        "action_name": "/navigate_to_pose",
                    }
                ],
            ),
            Node(
                condition=IfCondition(use_rviz),
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                arguments=["-d", rviz_config],
                parameters=[{"use_sim_time": use_sim_time}],
            ),
        ]
    )
