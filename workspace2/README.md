# ProMis Nav2 Runtime Workspace

This workspace contains a Python-first ROS 2 architecture for connecting
real-time ProMis probability landscapes to Nav2 navigation.

The current version is local-only and does not modify any GitHub remote.

## Packages

- `promis_runtime`: Python nodes and testable helpers.
  - publishes a rolling ProMis probability grid
  - converts probability to a Nav2-friendly occupancy/cost grid
  - provides a fake mobile base for RViz-only simulation
  - provides a simple static world map for simulation
- `promis_navigation`: launch, Nav2 parameters, mission config, and RViz config.

## Quick Start

From this workspace root:

```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch promis_navigation promis_rviz_sim.launch.py
```

In RViz:

1. Use `2D Nav Goal` to send a target.
2. Watch `/promis/probability_grid`, `/promis/cost_grid`, `/global_costmap/costmap`, and `/plan`.
3. The fake base integrates Nav2 `/cmd_vel` and publishes `/odom` plus `odom -> base_link`.

## Design

ProMis does not replace the geometric `/map`. Instead, `promis_map_node`
publishes a rolling semantic cost grid on `/promis/cost_grid`.

Nav2 consumes that grid through a second built-in `nav2_costmap_2d::StaticLayer`
named `promis_static_layer`, so this workspace can stay Python-only while still
using Nav2's C++ runtime internally.

## Real Robot Later

For LanderPi or another robot, keep `promis_map_node` and Nav2 config, then
replace the fake base with the robot's existing topics:

- `/odom`
- `/scan` if obstacle layers are enabled
- `/cmd_vel`
- TF tree containing `map`, `odom`, and `base_link`

