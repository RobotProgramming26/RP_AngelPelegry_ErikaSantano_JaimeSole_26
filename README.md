# RP_AngelPelegry_ErikaSantano_JaimeSole_26

# Robot Factory – ROS1 and ROS2 Integration

## 1. Project Overview

This project is the second part of the Robot Factory final assignment. It extends the original ROS1 game by adding services, parameters and a launch file, and integrates ROS1 with ROS2 using the `ros1_bridge`.

The project consists of a game developed with Python and Pygame, where the player controls a robot to collect different components while avoiding incorrect objects.

The main objectives are:
- Implement ROS1 services and parameters.
- Launch the different ROS1 nodes using a single launch file.
- Create communication between ROS1 and ROS2.
- Record ROS2 topic messages using rosbag.
- Extend the bridge to support custom messages and services (EXTRA).

## 2. Technologies Used

- Ubuntu 20.04
- ROS1 Noetic
- ROS2 Foxy
- Python 3
- Pygame
- ros1_bridge
- rosbag2
- Catkin and Colcon

## 3. Branch Structure

The project is divided into two independent workspaces:

```text
Part2_ROS1_ROS2/
│
├── robot_info_ws/                  # ROS1 workspace
│   └── src/
│       ├── robot_info/
│       │   ├── launch/
│       │   │   └── robot_info.launch
│       │   └── scripts/
│       │       ├── game_node.py
│       │       ├── info_user_node.py
│       │       ├── control_node.py
│       │       └── result_node.py
│       │
│       └── robotinfo_msgs/
│           ├── msg/
│           │   └── GameUserMsg.msg
│           └── srv/
│               ├── GetUserScore.srv
│               └── SetGameDifficulty.srv
│
└── robot_info2_ws/                 # ROS2 workspace
    └── src/
        ├── robot_info2/
        │   ├── robot_info2/
        │   │   └── robot_info2_node.py
        │   └── robot_info2.bag/     # Recorded ROS2 messages
        │
        └── robot_info_msgs/        # EXTRA
            ├── msg/
            │   └── GameUserMsg.msg
            ├── srv/
            │   ├── GetUserScore.srv
            │   └── SetGameDifficulty.srv
            └── mapping_rules.yaml
```

## 4. ROS1 Implementation

The ROS1 workspace contains the main game and its communication nodes.

### Nodes

| Node | Description |
|---|---|
| `game_node` | Runs the Pygame game, manages the game phases, parameters and services. |
| `info_user_node` | Requests the player's name, username, age and difficulty. Publishes the player information. |
| `control_node` | Reads keyboard inputs and publishes movement commands. |
| `result_game_node` | Receives the final score and requests the player's score percentage. |

### Custom Message

**GameUserMsg**

The custom message is used to transmit player information.

```text
string name
string username
int64 age
```

### Services

Two ROS1 services have been implemented:

| Service | Function |
|---|---|
| `/difficulty` | Changes the game difficulty to easy, medium or hard. |
| `/user_score` | Returns the percentage of the maximum score obtained by a player. |

The `/difficulty` service only accepts changes during the welcome phase.

The `/user_score` service returns `-1` if the requested username is unknown.

### Parameters

The following private parameters are managed by `game_node`:

| Parameter | Description |
|---|---|
| `/game_node/user_name` | Stores the current player's name. |
| `/game_node/change_player_color` | Changes the robot colour: 1 = Red, 2 = Purple, 3 = Blue. |
| `/game_node/screen_param` | Indicates the current game phase: phase1, phase2 or phase3. |

## 5. ROS2 Integration

The ROS2 workspace contains a listener node called `info_ros2_node`.

It receives keyboard commands published by the ROS1 `control_node` through the `/keyboard_control` topic.

The communication is established using `ros1_bridge`, which connects the two ROS versions.

### Main Topic

| Topic | Message type | Description |
|---|---|---|
| `/keyboard_control` | `std_msgs/String` | Transmits the robot movement commands: UP, DOWN, LEFT and RIGHT. |

The ROS2 listener displays the received commands and keeps track of the number of movements in each direction.

### Rosbag Recording

The `/keyboard_control` topic is recorded using ROS2 rosbag.

The recording is stored in:

```text
robot_info2_ws/src/robot_info2/robot_info2.bag/
```

This allows the communication to be inspected and replayed later.

## 6. EXTRA – Custom ROS1/ROS2 Bridge

As an additional part of the assignment, the project includes the ROS2 versions of the custom message and services.

The ROS1 package is called `robotinfo_msgs`, while the ROS2 package is called `robot_info_msgs`.

The `mapping_rules.yaml` file defines the correspondence between both packages so that `ros1_bridge` can recognize their message and service types.

The extra integration supports:

- `/user_information`: transmission of player information using `GameUserMsg`.
- `/difficulty`: changing the game difficulty from ROS2.
- `/user_score`: requesting the player's score from ROS2.

The ROS2 listener can also display the received player information.

This functionality requires building `ros1_bridge` from source with both custom interface packages available.

## 7. Building the Workspaces

The project was developed and tested using Ubuntu 20.04, ROS1 Noetic and ROS2 Foxy.

Build the ROS1 workspace:

```bash
source /opt/ros/noetic/setup.bash
cd ~/robot_info_ws
catkin_make
source devel/setup.bash
```

Build the ROS2 workspace in a separate terminal:

```bash
source /opt/ros/foxy/setup.bash
cd ~/robot_info2_ws
colcon build
source install/setup.bash
```

## 8. Running the Project

The complete system requires several terminals.

**Terminal 1 – ROS1 Game**

```bash
source /opt/ros/noetic/setup.bash
source ~/robot_info_ws/devel/setup.bash
roslaunch robot_info robot_info.launch
```

This launches the game and the ROS1 nodes.

**Terminal 2 – ROS1/ROS2 Bridge**

```bash
source /opt/ros/noetic/setup.bash
unset ROS_DISTRO
source /opt/ros/foxy/setup.bash
export ROS_MASTER_URI=http://localhost:11311

ros2 run ros1_bridge dynamic_bridge --bridge-all-1to2-topics
```

**Terminal 3 – ROS2 Listener**

```bash
source /opt/ros/foxy/setup.bash
source ~/robot_info2_ws/install/setup.bash

ros2 run robot_info2 robot_info2_node
```

**Terminal 4 – Rosbag Recording**

```bash
source /opt/ros/foxy/setup.bash
cd ~/robot_info2_ws/src/robot_info2

ros2 bag record -o robot_info2.bag /keyboard_control
```

Once all terminals are running, enter the player information in the `info_user_node` terminal and start playing using the arrow keys or WASD.

## 9. Testing Services and Parameters

Some useful commands to test the ROS1 implementation are:

```bash
rosparam list
rosparam get /game_node/screen_param
rosparam get /game_node/user_name

rosparam set /game_node/change_player_color 1

rosservice list
rosservice call /difficulty "change_difficulty: 'hard'"
rosservice call /user_score "username: 'angel'"
```

For ROS2, the following commands can be used:

```bash
ros2 topic echo /keyboard_control
ros2 bag info robot_info2.bag
ros2 service list
```

For the EXTRA functionality, the custom services can also be tested from ROS2.

## 10. Authors

Robot Factory – Final Assignment, Part II.

Universidad Carlos III de Madrid.
