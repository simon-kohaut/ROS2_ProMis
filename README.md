# ProMis → Nav2 Integration: Running Robot Navigation in RViz

## 1. System Overview

This setup enables a Turtlebot3 robot in Gazebo to navigate using a map generated from ProMis.

Pipeline:

```text
ProMis → OccupancyGrid (/map) → Nav2 → Robot Motion (Gazebo)
```

---

## 2. Prerequisites

Make sure the following components are available:

* ProMis-generated grid (`.npy`)
* Metadata file (`.yaml`)
* ROS2 workspace built (`colcon build`)
* `promis_costmap_publisher` implemented
* Turtlebot3 packages installed
* Nav2 installed

---

## 3. Launch the Full System

### Terminal 1: Start Gazebo

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

---

### Terminal 2: Start Nav2

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=True
```

---

### Terminal 3: Publish ProMis Map

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 run promis_nav2_bridge promis_costmap_publisher \
  --ros-args \
  -p grid_npy:=/path/to/promis_prob_grid.npy \
  -p meta_yaml:=/path/to/promis_grid_meta.yaml \
  -p topic:=/map
```

---

### Terminal 4: Publish TF (if needed)

```bash
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map odom
```

---

### Terminal 5: Start RViz

```bash
rviz2
```

---

## 4. Configure RViz

Set:

```text
Fixed Frame = map
```

Add the following displays:

```text
Map (Topic: /map)
RobotModel
TF
LaserScan (optional)
Path (optional)
```

Adjust visualization:

```text
Map Alpha ≈ 0.2–0.5 (to make robot visible)
TF → Show Names (optional)
```

---

## 5. Verify System State

Before sending any goal, confirm:

### 5.1 Map is visible

* `/map` is displayed correctly
* Size and position match metadata

---

### 5.2 Robot is visible

* RobotModel appears in RViz
* TF frames (`base_link`, `odom`, `map`) are present

---

### 5.3 TF chain is valid

```text
map → odom → base_link
```

Check:

```bash
ros2 run tf2_ros tf2_echo map base_link
```

---

## 6. Send Navigation Goal in RViz

In RViz:

```text
Click: 2D Goal Pose
```

Then:

```text
Click and drag on the map to set:
- Position (click)
- Orientation (drag direction)
```

---

## 7. Expected Behavior

If the system is correctly configured:

### In RViz

* A path appears (`/plan`)
* The robot orientation updates
* Path visualization is visible

---

### In ROS topics

```bash
ros2 topic echo /plan
ros2 topic echo /cmd_vel
```

You should see:

```text
/plan    → path data
/cmd_vel → velocity commands
```

---

## 8. Recommended Goal Selection

For initial testing:

* Choose a goal close to the robot
* Avoid edges of the map
* Avoid high-cost or blocked regions
* Use clearly free areas

Example:

```text
Robot position ≈ (-2, -0.5)

Try goals like:
(-1, -0.5)
(-2, 0.5)
(-1, 0.5)
```

