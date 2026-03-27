# robot_platform

`robot_platform` is a ROS 2 Python package that provides a robot-agnostic integration layer for mobile robots.

The package standardizes a small set of topics so that upper-layer modules do not need to know the exact model-specific topic names:

- `/platform/cmd_vel`
- `/platform/odom`
- `/platform/scan`
- `/platform/status`
- `/platform/goal_pose`
- `/platform/navigation_status`
- `/platform/navigation_feedback`
- `/platform/cancel_navigation`

## Why this package exists

Your current stack already proved this chain:

`ProMis -> grid map -> ROS map_server -> Nav2 planner`

The next engineering step is not another one-off demo. It is a stable interface layer that lets different robots plug into the same navigation stack with minimal changes.

This package does that by splitting the problem into two parts:

1. A common platform API for commands, state, and goals.
2. Per-robot adapters that translate model-specific topics into that common API.

## Built-in adapters

- `generic_mobile_base`
- `differential_drive`
- `turtlebot3`

`differential_drive` is an alias for the generic mobile-base adapter.

## Architecture

### 1. Platform Router Node

`platform_router` is the topic adapter node.

It:

- subscribes to `/platform/cmd_vel`
- publishes to the robot-specific `cmd_vel` topic
- subscribes to the robot-specific `odom` and `scan` topics
- republishes them to `/platform/odom` and `/platform/scan`
- publishes periodic JSON status on `/platform/status`

### 2. Nav2 Goal Bridge Node

`nav2_goal_bridge` is the navigation interface node.

It:

- subscribes to `/platform/goal_pose`
- forwards goals to Nav2 `/navigate_to_pose`
- publishes lifecycle/result updates on `/platform/navigation_status`
- publishes feedback on `/platform/navigation_feedback`
- listens for `/platform/cancel_navigation`

## Quick start

Build in a ROS 2 workspace:

```bash
colcon build --packages-select robot_platform
source install/setup.bash
```

Launch with the generic adapter:

```bash
ros2 launch robot_platform bringup.launch.py robot_type:=generic_mobile_base
```

Launch with TurtleBot3 defaults:

```bash
ros2 launch robot_platform bringup.launch.py robot_type:=turtlebot3
```

Publish a generic velocity command:

```bash
ros2 topic pub /platform/cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.2}, angular: {z: 0.0}}"
```

Send a navigation goal through the platform API:

```bash
ros2 topic pub --once /platform/goal_pose geometry_msgs/msg/PoseStamped \
"{header: {frame_id: map}, pose: {position: {x: 10.0, y: 10.0, z: 0.0}, orientation: {w: 1.0}}}"
```

## Extending to a new robot

The platform is only truly robot-agnostic if new robots can be added without rewriting the upper layer.

To add a new robot:

1. Create a new adapter class under `robot_platform/adapters/`.
2. Inherit from `RobotAdapter`.
3. Provide the default topics and frames for that robot.
4. Register the adapter in `robot_platform/registry.py`.

If a robot does not use `geometry_msgs/Twist` for motion control, add a dedicated adapter node for that robot and keep the `/platform/*` API unchanged.

## Validation workflows

This repository now includes validation assets for two complementary checks:

1. Planner-only validation of the ProMis handoff into Nav2.
2. End-to-end TurtleBot3 simulation with `robot_platform` in the loop.

### Included validation maps

Two deterministic example maps live under `maps/promis_validation/`:

- `top_preferred.yaml`
- `bottom_preferred.yaml`

They are geometrically symmetric and swap which corridor remains navigable. This keeps the regression deterministic: the same start and goal should produce a top-corridor path on one map and a bottom-corridor path on the other.

### Planner-only validation

This validates the planning semantics without requiring odometry or a running robot.

In WSL / ROS 2 Humble:

```bash
source /opt/ros/humble/setup.bash
cd "/mnt/c/Users/rensh/Documents/New project"
colcon build --packages-select robot_platform
source install/setup.bash

ros2 launch robot_platform promis_planner_validation.launch.py
```

In a second terminal:

```bash
source /opt/ros/humble/setup.bash
cd "/mnt/c/Users/rensh/Documents/New project"
source install/setup.bash

validate_nav2_path --expected-corridor top
```

To validate the opposite bias:

```bash
source /opt/ros/humble/setup.bash
cd "/mnt/c/Users/rensh/Documents/New project"
source install/setup.bash

PKG_SHARE=$(ros2 pkg prefix robot_platform)/share/robot_platform
ros2 launch robot_platform promis_planner_validation.launch.py \
  map:=$PKG_SHARE/maps/promis_validation/bottom_preferred.yaml
```

Then:

```bash
validate_nav2_path --expected-corridor bottom
```

The CLI prints a JSON summary including `path_length_m`, `average_y`, and the inferred corridor.

### TurtleBot3 integration validation

This validates that Nav2 goals can flow through `/platform/goal_pose`, that Nav2 command output is routed through `/platform/cmd_vel`, and that `platform_router` republishes robot state on `/platform/odom` and `/platform/scan`.

```bash
source /opt/ros/humble/setup.bash
cd "/mnt/c/Users/rensh/Documents/New project"
colcon build --packages-select robot_platform
source install/setup.bash

ros2 launch robot_platform promis_turtlebot3_validation.launch.py
```

The default spawn pose is `(-9.0, 0.0)` on the validation map, so a matching goal is:

```bash
ros2 topic pub --once /platform/goal_pose geometry_msgs/msg/PoseStamped \
"{header: {frame_id: map}, pose: {position: {x: 9.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}"
```

Useful checks:

```bash
ros2 topic echo /platform/status --once
ros2 topic echo /platform/navigation_status
ros2 topic echo /platform/navigation_feedback
ros2 topic echo /platform/scan --once
ros2 topic echo /platform/odom --once
```

### Notes on fidelity

The validation harness intentionally uses the same file-level handoff semantics as the current ProMis notebook:

- `probability -> cost` uses `cost = 254 * (1 - probability)`
- `cost -> PGM` uses `pixel = 255 - cost`
- map YAML uses `mode: scale`

This is a good v1 validation path because it keeps the ROS-side contract identical to the current notebook export: static `map.pgm` + `map.yaml` loaded by `nav2_map_server`. The bundled sample maps are deterministic regression assets, not literal ProMis outputs. If stricter fidelity is required later, the next step is a custom costmap layer or a direct occupancy / cost publisher rather than the PGM handoff.
