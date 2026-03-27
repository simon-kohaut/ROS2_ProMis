from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    robot_type = LaunchConfiguration("robot_type")
    robot_name = LaunchConfiguration("robot_name")
    use_nav2_bridge = LaunchConfiguration("use_nav2_bridge")
    enable_scan = LaunchConfiguration("enable_scan")
    cmd_vel_topic = LaunchConfiguration("cmd_vel_topic")
    odom_topic = LaunchConfiguration("odom_topic")
    scan_topic = LaunchConfiguration("scan_topic")
    global_frame = LaunchConfiguration("global_frame")
    odom_frame = LaunchConfiguration("odom_frame")
    base_frame = LaunchConfiguration("base_frame")
    platform_cmd_vel_topic = LaunchConfiguration("platform_cmd_vel_topic")
    platform_odom_topic = LaunchConfiguration("platform_odom_topic")
    platform_scan_topic = LaunchConfiguration("platform_scan_topic")
    platform_status_topic = LaunchConfiguration("platform_status_topic")
    goal_topic = LaunchConfiguration("goal_topic")
    cancel_topic = LaunchConfiguration("cancel_topic")
    navigation_status_topic = LaunchConfiguration("navigation_status_topic")
    navigation_feedback_topic = LaunchConfiguration("navigation_feedback_topic")
    action_name = LaunchConfiguration("action_name")

    return LaunchDescription(
        [
            DeclareLaunchArgument("robot_type", default_value="generic_mobile_base"),
            DeclareLaunchArgument("robot_name", default_value="robot"),
            DeclareLaunchArgument("use_nav2_bridge", default_value="true"),
            DeclareLaunchArgument("enable_scan", default_value="true"),
            DeclareLaunchArgument("cmd_vel_topic", default_value=""),
            DeclareLaunchArgument("odom_topic", default_value=""),
            DeclareLaunchArgument("scan_topic", default_value=""),
            DeclareLaunchArgument("global_frame", default_value=""),
            DeclareLaunchArgument("odom_frame", default_value=""),
            DeclareLaunchArgument("base_frame", default_value=""),
            DeclareLaunchArgument("platform_cmd_vel_topic", default_value="/platform/cmd_vel"),
            DeclareLaunchArgument("platform_odom_topic", default_value="/platform/odom"),
            DeclareLaunchArgument("platform_scan_topic", default_value="/platform/scan"),
            DeclareLaunchArgument("platform_status_topic", default_value="/platform/status"),
            DeclareLaunchArgument("goal_topic", default_value="/platform/goal_pose"),
            DeclareLaunchArgument("cancel_topic", default_value="/platform/cancel_navigation"),
            DeclareLaunchArgument("navigation_status_topic", default_value="/platform/navigation_status"),
            DeclareLaunchArgument("navigation_feedback_topic", default_value="/platform/navigation_feedback"),
            DeclareLaunchArgument("action_name", default_value="/navigate_to_pose"),
            Node(
                package="robot_platform",
                executable="platform_router",
                name="platform_router",
                output="screen",
                parameters=[
                    {
                        "robot_type": robot_type,
                        "robot_name": robot_name,
                        "enable_scan": enable_scan,
                        "cmd_vel_topic": cmd_vel_topic,
                        "odom_topic": odom_topic,
                        "scan_topic": scan_topic,
                        "global_frame": global_frame,
                        "odom_frame": odom_frame,
                        "base_frame": base_frame,
                        "platform_cmd_vel_topic": platform_cmd_vel_topic,
                        "platform_odom_topic": platform_odom_topic,
                        "platform_scan_topic": platform_scan_topic,
                        "platform_status_topic": platform_status_topic,
                    }
                ],
            ),
            Node(
                condition=IfCondition(use_nav2_bridge),
                package="robot_platform",
                executable="nav2_goal_bridge",
                name="nav2_goal_bridge",
                output="screen",
                parameters=[
                    {
                        "goal_topic": goal_topic,
                        "cancel_topic": cancel_topic,
                        "status_topic": navigation_status_topic,
                        "feedback_topic": navigation_feedback_topic,
                        "action_name": action_name,
                    }
                ],
            ),
        ]
    )
