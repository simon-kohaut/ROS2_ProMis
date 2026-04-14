from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_width_m = LaunchConfiguration("map_width_m")
    map_height_m = LaunchConfiguration("map_height_m")
    map_resolution_m = LaunchConfiguration("map_resolution_m")
    initial_x = LaunchConfiguration("initial_x")
    initial_y = LaunchConfiguration("initial_y")
    initial_yaw = LaunchConfiguration("initial_yaw")

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("map_width_m", default_value="60.0"),
            DeclareLaunchArgument("map_height_m", default_value="60.0"),
            DeclareLaunchArgument("map_resolution_m", default_value="0.1"),
            DeclareLaunchArgument("initial_x", default_value="0.0"),
            DeclareLaunchArgument("initial_y", default_value="0.0"),
            DeclareLaunchArgument("initial_yaw", default_value="0.0"),
            Node(
                package="promis_runtime",
                executable="static_world_map_node",
                name="static_world_map_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "map_topic": "/map",
                        "frame_id": "map",
                        "width_m": map_width_m,
                        "height_m": map_height_m,
                        "resolution_m": map_resolution_m,
                    }
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
            Node(
                package="promis_runtime",
                executable="fake_base_node",
                name="fake_base_node",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "cmd_vel_topic": "/cmd_vel",
                        "odom_topic": "/odom",
                        "odom_frame": "odom",
                        "base_frame": "base_link",
                        "initial_x": initial_x,
                        "initial_y": initial_y,
                        "initial_yaw": initial_yaw,
                    }
                ],
            ),
        ]
    )
