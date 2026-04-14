

# I. Map File Preparation

## 1. Create directories

```bash
mkdir -p ~/promis_nav2_maps/darmstadt_map
mkdir -p ~/promis_nav2_maps/config
```

## 2. Copy map files from Windows to WSL

Your source path:

```text
C:\Users\rensh\Desktop\CE Semester 7\Simon Kohaut\code
```

In WSL:

```bash
cp "/mnt/c/Users/rensh/Desktop/CE Semester 7/Simon Kohaut/code/map.pgm" \
   ~/promis_nav2_maps/darmstadt_map/

cp "/mnt/c/Users/rensh/Desktop/CE Semester 7/Simon Kohaut/code/map.yaml" \
   ~/promis_nav2_maps/darmstadt_map/
```

## 3. Verify files

```bash
ls ~/promis_nav2_maps/darmstadt_map
```

Expected:

```text
map.pgm  map.yaml
```

---

# II. Create Map Server Parameter File

## 1. Edit file

```bash
nano ~/promis_nav2_maps/config/map_server_params.yaml
```

Content:

```yaml
map_server:
  ros__parameters:
    yaml_filename: /home/xiaoyuweng/promis_nav2_maps/darmstadt_map/map.yaml

lifecycle_manager:
  ros__parameters:
    use_sim_time: false
    autostart: true
    node_names: ['map_server']
```

Save and exit.

## 2. Verify

```bash
cat ~/promis_nav2_maps/config/map_server_params.yaml
```

---

# III. Start Map Display Pipeline

## Terminal 1: map_server

```bash
source /opt/ros/humble/setup.bash

ros2 run nav2_map_server map_server \
--ros-args \
--params-file ~/promis_nav2_maps/config/map_server_params.yaml
```

## Terminal 2: lifecycle_manager

```bash
source /opt/ros/humble/setup.bash

ros2 run nav2_lifecycle_manager lifecycle_manager \
--ros-args \
--params-file ~/promis_nav2_maps/config/map_server_params.yaml
```

## Terminal 3: check topics

```bash
source /opt/ros/humble/setup.bash
ros2 topic list
```

Expected:

```text
/map
/map_server/transition_event
```

## Terminal 3: check map data

```bash
source /opt/ros/humble/setup.bash
ros2 topic echo /map --once
```

Expected fields:

* resolution: 1.0
* width: 200
* height: 200
* origin.x: -100
* origin.y: -100

---

# IV. Open RViz and Display Map

## Terminal 4

```bash
source /opt/ros/humble/setup.bash
rviz2
```

## RViz actions (not commands)

1. Set `Fixed Frame` to `map`
2. Click `Add`
3. Choose `By topic`
4. Select `/map`
5. Set QoS:

   * Reliability = Reliable
   * Durability = Transient Local

Optional:

* Change view to `TopDownOrtho`

---

# V. Add Minimal TF Tree

## Terminal 5: map → odom

```bash
source /opt/ros/humble/setup.bash

ros2 run tf2_ros static_transform_publisher \
--x 0 --y 0 --z 0 \
--roll 0 --pitch 0 --yaw 0 \
--frame-id map \
--child-frame-id odom
```

## Terminal 6: odom → base_link

```bash
source /opt/ros/humble/setup.bash

ros2 run tf2_ros static_transform_publisher \
--x 0 --y 0 --z 0 \
--roll 0 --pitch 0 --yaw 0 \
--frame-id odom \
--child-frame-id base_link
```

Keep both terminals running.

---

# VI. Create Navigation Parameter File

## 1. Create file

```bash
nano ~/promis_nav2_maps/config/nav2_navigation_only.yaml
```

Paste the full YAML content (same as before).

---

# VII. Launch Nav2 Navigation

Do NOT stop:

* map_server
* lifecycle_manager
* static TF

## New terminal

```bash
source /opt/ros/humble/setup.bash

ros2 launch nav2_bringup navigation_launch.py \
use_sim_time:=false \
params_file:=/home/xiaoyuweng/promis_nav2_maps/config/nav2_navigation_only.yaml
```

---

# VIII. Verify Nav2

## Nodes

```bash
ros2 node list
```

Expect:

* /planner_server
* /controller_server
* /bt_navigator
* /behavior_server

## Costmap topics

```bash
ros2 topic list | grep costmap
```

## Plan topics

```bash
ros2 topic list | grep plan
```

## Actions

```bash
ros2 action list
```

---

# IX. RViz Setup for Navigation

Add:

* Map → /map
* Map → /global_costmap/costmap
* Map → /local_costmap/costmap
* TF
* Path → /plan

Optional:

* Path → /plan_smoothed

---

# X. Send Navigation Goal

## Navigate

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
"{pose: {header: {frame_id: map}, pose: {position: {x: 10.0, y: 10.0, z: 0.0}, orientation: {w: 1.0}}}}"
```

## Check path

```bash
ros2 topic echo /plan --once
```

---

# XI. Pure Planning (Recommended)

```bash
ros2 action send_goal /compute_path_to_pose nav2_msgs/action/ComputePathToPose \
"{goal: {header: {frame_id: map}, pose: {position: {x: 10.0, y: 10.0, z: 0.0}, orientation: {w: 1.0}}}, start: {header: {frame_id: map}, pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}, use_start: true}"
```

---

# XII. Controller Abort Explanation

Logs:

```text
[follow_path] [ActionServer] Aborting handle.
```

Meaning:

* Planning succeeded
* Execution failed due to no odometry

---

# XIII. Stop Commands

```bash
Ctrl + C
```

Stop all running terminals if needed.

---

# XIV. Minimal Re-run Sequence

## A. Map

```bash
ros2 run nav2_map_server map_server --ros-args --params-file ~/promis_nav2_maps/config/map_server_params.yaml
```

```bash
ros2 run nav2_lifecycle_manager lifecycle_manager --ros-args --params-file ~/promis_nav2_maps/config/map_server_params.yaml
```

## B. TF

```bash
ros2 run tf2_ros static_transform_publisher --frame-id map --child-frame-id odom ...
```

```bash
ros2 run tf2_ros static_transform_publisher --frame-id odom --child-frame-id base_link ...
```

## C. Nav2

```bash
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=false params_file:=...
```

## D. RViz

```bash
rviz2
```

## E. Goal

```bash
ros2 action send_goal /navigate_to_pose ...
```

## F. Plan

```bash
ros2 topic echo /plan --once
```

---

