---

# **Overall Diagram**

```text
[doc/source/notebooks/usage.ipynb]
    |
    | Generate ProMis probabilistic semantic field / landscape
    | Rasterize probability grid
    | probability -> cost
    | cost -> ROS map.pgm + map.yaml
    v
[maps/promis_validation/top_preferred.yaml]
[maps/promis_validation/bottom_preferred.yaml]
    |
    | Loaded by map_server
    v
[launch/promis_planner_validation.launch.py]
    |
    | Starts nodes:
    | - nav2_map_server/map_server
    | - nav2_lifecycle_manager/lifecycle_manager_map
    | - tf2_ros/static_transform_publisher (map -> odom)
    | - tf2_ros/static_transform_publisher (odom -> base_link)
    | - include launch/nav2_validation.launch.py
    v
/topic: /map
/topic: /tf
/topic: /tf_static
    |
    v
[launch/nav2_validation.launch.py]
    |
    | Reads:
    | - config/promis_validation_nav2.yaml
    |
    | Starts nodes:
    | - nav2_controller/controller_server
    | - nav2_smoother/smoother_server
    | - nav2_planner/planner_server
    | - nav2_behaviors/behavior_server
    | - nav2_bt_navigator/bt_navigator
    | - nav2_waypoint_follower/waypoint_follower
    | - nav2_velocity_smoother/velocity_smoother
    | - nav2_lifecycle_manager/lifecycle_manager_navigation
    v
/action: /compute_path_to_pose
/action: /navigate_to_pose
/topic: /plan
/topic: /global_costmap/costmap
/topic: /local_costmap/costmap
    |
    | Nav2 is NOT directly bound to robot-specific topics
    | It uses a unified platform interface layer
    v
[config/promis_validation_nav2.yaml]
    |
    | Key bindings:
    | - global/local obstacle layer reads /platform/scan
    | - velocity_smoother reads /platform/odom
    | - velocity_smoother outputs to /platform/cmd_vel
    v
/topic: /platform/scan
/topic: /platform/odom
/topic: /platform/cmd_vel
    ^
    |
    | Provided by platform layer
    |
[launch/bringup.launch.py]
    |
    | Starts nodes:
    | - robot_platform/platform_router
    | - robot_platform/nav2_goal_bridge (optional)
    v
[robot_platform/platform_router_node.py]
    |
    | Reads robot_type
    | -> calls registry.py
    | -> selects adapters/*
    v
[robot_platform/registry.py]
    |
    | Available adapters:
    | - generic_mobile_base
    | - differential_drive
    | - turtlebot3
    v
[robot_platform/adapters/base.py]
[robot_platform/adapters/generic_mobile_base.py]
[robot_platform/adapters/turtlebot3.py]
    |
    | Defines real robot topics/frames:
    | - /cmd_vel
    | - /odom
    | - /scan
    | - map / odom / base_link
    v
[Node: platform_router]
    |
    | Subscribes: /platform/cmd_vel
    | Publishes: <robot cmd_vel> e.g. /cmd_vel
    |
    | Subscribes: <robot odom> e.g. /odom
    | Publishes: /platform/odom
    |
    | Subscribes: <robot scan> e.g. /scan
    | Publishes: /platform/scan
    |
    | Publishes: /platform/status
    v
/topic: /platform/status
```

---

# **Navigation Action Bridge Diagram**

```text
User / High-level task module
    |
    | Publishes navigation goal
    v
/topic: /platform/goal_pose
    |
    v
[robot_platform/nav2_goal_bridge_node.py]
    |
    | ActionClient -> /navigate_to_pose
    v
/action: /navigate_to_pose
    |
    | Handled by bt_navigator / planner / controller
    v
[Nav2 stack]
    |
    | Outputs:
    | - /plan
    | - navigation feedback
    | - navigation result
    v
[Node: nav2_goal_bridge]
    |
    | Publishes:
    | - /platform/navigation_status
    | - /platform/navigation_feedback
    |
    | Subscribes:
    | - /platform/cancel_navigation
    v
/action cancel for /navigate_to_pose
```

---

# **Pure Planning Validation Flow**

```text
[launch/promis_planner_validation.launch.py]
    |
    v
/action: /compute_path_to_pose
    ^
    |
[robot_platform/validation.py]
    |
    | Sends ComputePathToPose request:
    | - start_x / start_y
    | - goal_x / goal_y
    |
    | Reads returned path
    | Computes:
    | - pose_count
    | - path_length_m
    | - average_y
    | - corridor = top or bottom
    v
JSON summary
    |
    | Compared with expected corridor
    v
Verify whether ProMis map changes path preference
```

---

# **Gazebo / TurtleBot3 Integration**

```text
[launch/promis_turtlebot3_validation.launch.py]
    |
    | Starts:
    | - turtlebot3_gazebo/empty_world.launch.py
    | - map_server
    | - platform bringup
    | - nav2_validation.launch.py
    v
[Gazebo TurtleBot3]
    |
    | Provides simulation topics:
    | - /odom
    | - /scan
    | - TF / base_link
    v
[platform_router]
    |
    | Converts to unified interface:
    | - /platform/odom
    | - /platform/scan
    | - /platform/cmd_vel
    v
[Nav2 stack]
    |
    | Uses unified interface for planning and control
    v
Robot executes motion in simulation
```

---

# **Compressed Main Pipeline**

```text
usage.ipynb
    -> generate semantic map
    -> export .pgm/.yaml
    -> map_server publishes /map
    -> Nav2 plans using /map + /platform/odom + /platform/scan
    -> platform_router unifies robot interfaces
    -> nav2_goal_bridge unifies navigation goal/action
    -> validation.py checks whether path reflects top/bottom semantic preference
    -> promis_turtlebot3_validation.launch.py runs full simulation validation
```

---

# **Minimal “File Responsibility” Memory Map**

* `usage.ipynb`: generate map
* `promis_planner_validation.launch.py`: validate planner first
* `nav2_validation.launch.py`: start Nav2 core
* `bringup.launch.py`: start platform interface layer
* `platform_router_node.py`: unify topics
* `nav2_goal_bridge_node.py`: unify navigation actions
* `validation.py`: evaluate whether path matches semantic preference
* `promis_turtlebot3_validation.launch.py`: run full Gazebo + TurtleBot3 pipeline

---
