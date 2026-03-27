import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    package_dir = get_package_share_directory("robot_platform")
    turtlebot3_gazebo_dir = get_package_share_directory("turtlebot3_gazebo")

    turtlebot3_model = LaunchConfiguration("turtlebot3_model")
    map_path = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")
    use_sim_time = LaunchConfiguration("use_sim_time")
    autostart = LaunchConfiguration("autostart")
    log_level = LaunchConfiguration("log_level")
    x_pose = LaunchConfiguration("x_pose")
    y_pose = LaunchConfiguration("y_pose")

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo_dir, "launch", "empty_world.launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "x_pose": x_pose,
            "y_pose": y_pose,
        }.items(),
    )

    platform_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(package_dir, "launch", "bringup.launch.py")),
        launch_arguments={
            "robot_type": "turtlebot3",
            "robot_name": "tb3_validation",
            "use_nav2_bridge": "true",
            "enable_scan": "true",
            "cmd_vel_topic": "/cmd_vel",
            "odom_topic": "/odom",
            "scan_topic": "/scan",
            "base_frame": "base_link",
            "goal_topic": "/platform/goal_pose",
            "navigation_status_topic": "/platform/navigation_status",
            "navigation_feedback_topic": "/platform/navigation_feedback",
            "action_name": "/navigate_to_pose",
        }.items(),
    )

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_dir, "launch", "nav2_validation.launch.py")
        ),
        launch_arguments={
            "params_file": params_file,
            "use_sim_time": use_sim_time,
            "autostart": autostart,
            "log_level": log_level,
        }.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("turtlebot3_model", default_value="burger"),
            DeclareLaunchArgument(
                "map",
                default_value=os.path.join(
                    package_dir,
                    "maps",
                    "promis_validation",
                    "top_preferred.yaml",
                ),
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=os.path.join(
                    package_dir,
                    "config",
                    "promis_validation_nav2.yaml",
                ),
            ),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("autostart", default_value="true"),
            DeclareLaunchArgument("log_level", default_value="info"),
            DeclareLaunchArgument("x_pose", default_value="-9.0"),
            DeclareLaunchArgument("y_pose", default_value="0.0"),
            SetEnvironmentVariable("TURTLEBOT3_MODEL", turtlebot3_model),
            gazebo_launch,
            Node(
                package="nav2_map_server",
                executable="map_server",
                name="map_server",
                output="screen",
                parameters=[
                    {"yaml_filename": map_path},
                    {"use_sim_time": use_sim_time},
                ],
            ),
            Node(
                package="nav2_lifecycle_manager",
                executable="lifecycle_manager",
                name="lifecycle_manager_map",
                output="screen",
                parameters=[
                    {"use_sim_time": use_sim_time},
                    {"autostart": autostart},
                    {"node_names": ["map_server"]},
                ],
            ),
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="map_to_odom",
                arguments=[
                    "--x",
                    "0",
                    "--y",
                    "0",
                    "--z",
                    "0",
                    "--roll",
                    "0",
                    "--pitch",
                    "0",
                    "--yaw",
                    "0",
                    "--frame-id",
                    "map",
                    "--child-frame-id",
                    "odom",
                ],
            ),
            platform_launch,
            nav2_launch,
        ]
    )
