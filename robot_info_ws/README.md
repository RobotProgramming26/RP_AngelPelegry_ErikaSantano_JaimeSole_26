# Robot Factory — ROS Final Work, Part II
ROS1 services, parameters and launcher + ROS2 listener over `ros1_bridge`.

Tested setup: **Ubuntu 20.04, ROS1 Noetic + ROS2 Foxy** (the combination that ships
`ros1_bridge` as a binary). For Humble, the same steps apply, but the bridge must be
built from source (see the EXTRA section).

---

## 1. Repository structure

```
catkin_ws/                       # ROS1 workspace
└── src/
    ├── robot_info/              # ROS1 nodes (was game_pr in Part I)
    │   ├── CMakeLists.txt
    │   ├── package.xml
    │   ├── launch/
    │   │   └── robot_info.launch
    │   └── scripts/
    │       ├── game_node.py         # game + services /user_score, /difficulty + params
    │       ├── info_user_node.py    # player data + /difficulty client
    │       ├── control_node.py      # keyboard -> /keyboard_control
    │       └── result_node.py       # result_game_node + /user_score client
    └── robotinfo_msgs/          # custom msg + srv (was game_msgs in Part I)
        ├── CMakeLists.txt
        ├── package.xml
        ├── msg/GameUserMsg.msg
        └── srv/
            ├── GetUserScore.srv
            └── SetGameDifficulty.srv

ros2_ws/                         # ROS2 workspace
└── src/
    ├── robot_info2/             # ROS2 listener (ament_python)
    │   ├── package.xml
    │   ├── setup.py
    │   ├── setup.cfg
    │   ├── resource/robot_info2
    │   ├── robot_info2/
    │   │   ├── __init__.py
    │   │   └── robot_info2_node.py   # node "info_ros2_node"
    │   └── robot_info2.bag/          # rosbag recorded from ROS2 (generated)
    └── robot_info_msgs/         # EXTRA: ROS2 copy of the msg/srv for the bridge
        ├── CMakeLists.txt
        ├── package.xml
        ├── mapping_rules.yaml
        ├── msg/GameUserMsg.msg
        └── srv/{GetUserScore.srv, SetGameDifficulty.srv}
```

---

## 2. Dependencies

```bash
sudo apt update
sudo apt install python3-pygame xterm            # game window + terminals for the launcher
sudo apt install ros-foxy-ros1-bridge            # binary bridge (Noetic <-> Foxy)
sudo apt install ros-foxy-rosbag2 ros-foxy-ros2bag ros-foxy-rosbag2-storage-default-plugins
```

> Never source ROS1 and ROS2 in the same terminal, **except** in the bridge terminal.

---

## 3. Build

**ROS1** (terminal with only Noetic sourced):
```bash
source /opt/ros/noetic/setup.bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

**ROS2** (new terminal with only Foxy sourced):
```bash
source /opt/ros/foxy/setup.bash
cd ~/ros2_ws
colcon build --packages-select robot_info2          # add robot_info_msgs for the EXTRA
source install/setup.bash
```

---

## 4. Run the complete ROS1 game (launcher)

```bash
source /opt/ros/noetic/setup.bash && source ~/catkin_ws/devel/setup.bash
roslaunch robot_info robot_info.launch
```

- Starts `roscore` (if needed), `game_node`, `info_user_node`, `control_node` and `result_game_node`.
- `info_user_node` and `control_node` open in their own **xterm** windows because they read the keyboard.
  To use gnome-terminal instead: `roslaunch robot_info robot_info.launch term:="gnome-terminal --wait --"`
- Initial player colour: `roslaunch robot_info robot_info.launch player_color:=3`

Flow: type name, username, age and difficulty in the *info_user_node* window → the game shows
the Welcome screen for 4 s → click the *control_node* window and play with arrow keys / WASD →
at the end `result_game_node` prints the score and the percentage returned by `/user_score`.

### Running each node separately (alternative)
```bash
roscore
rosrun robot_info game_node.py
rosrun robot_info info_user_node.py
rosrun robot_info control_node.py
rosrun robot_info result_node.py
```

---

## 5. Services (server: `game_node`, types in `robotinfo_msgs/srv`)

| Service | Type | Request → Response |
|---|---|---|
| `/user_score` | `GetUserScore` | `string username` → `int64 score` = % of the max score (380 pts = 100 %), `-1` if the user is unknown |
| `/difficulty` | `SetGameDifficulty` | `string change_difficulty` (`easy`/`medium`/`hard`) → `bool success` (`True` only in phase1) |

Clients: `result_game_node` calls `/user_score` when the final score arrives;
`info_user_node` calls `/difficulty` before publishing the player data. Manual test:
```bash
rosservice call /difficulty "change_difficulty: 'hard'"    # True only on the Welcome screen
rosservice call /user_score "username: 'myuser'"
```
Difficulty multiplies the falling speed, spawn interval, wrong-item ratio and level time
(`medium` = original Part I values).

---

## 6. Parameters (private to `game_node` → `/game_node/<name>`)

| Parameter | Type | Function |
|---|---|---|
| `user_name` | string | Player's name (written when `/user_information` arrives) |
| `change_player_color` | int | 1 = Red, 2 = Purple, 3 = Blue — read twice per second, changes live |
| `screen_param` | string | Current phase: `phase1` (Welcome), `phase2` (Game), `phase3` (Final) |

```bash
rosparam list
rosparam get /game_node/screen_param
rosparam set /game_node/change_player_color 1
```

---

## 7. ROS2: ros1_bridge + `robot_info2_node` + rosbag

Terminal A – ROS1 game: `roslaunch robot_info robot_info.launch`

Terminal B – bridge (both distros sourced, ROS1 first):
```bash
source /opt/ros/noetic/setup.bash
source /opt/ros/foxy/setup.bash
export ROS_MASTER_URI=http://localhost:11311
ros2 run ros1_bridge dynamic_bridge --bridge-all-1to2-topics
```

Terminal C – ROS2 listener:
```bash
source /opt/ros/foxy/setup.bash && source ~/ros2_ws/install/setup.bash
ros2 run robot_info2 robot_info2_node
```

Terminal D – record the bag (inside the robot_info2 package):
```bash
source /opt/ros/foxy/setup.bash
cd ~/ros2_ws/src/robot_info2
ros2 bag record -o robot_info2.bag /keyboard_control      # Ctrl+C to stop
ros2 bag info robot_info2.bag
ros2 bag play robot_info2.bag                              # replay check
```

---

## 8. EXTRA – bridging the custom msg and srv (bridge built from source)

1. Build `robotinfo_msgs` (catkin) and `robot_info_msgs` (colcon) as in section 3.
2. Build the bridge in its own workspace with **everything** sourced:
```bash
mkdir -p ~/bridge_ws/src && cd ~/bridge_ws/src
git clone -b foxy https://github.com/ros2/ros1_bridge.git      # use -b humble... for Humble
cd ~/bridge_ws
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
source /opt/ros/foxy/setup.bash
source ~/ros2_ws/install/local_setup.bash
colcon build --symlink-install --packages-select ros1_bridge --cmake-force-configure
```
3. Check the pairs and run it:
```bash
source ~/bridge_ws/install/local_setup.bash
ros2 run ros1_bridge dynamic_bridge --print-pairs | grep -i robot
ros2 run ros1_bridge dynamic_bridge --bridge-all-topics
```
`mapping_rules.yaml` tells the bridge that ROS1 `robotinfo_msgs` = ROS2 `robot_info_msgs`.
With it, `robot_info2_node` also prints `/user_information`, and the ROS1 services can be called from ROS2:
```bash
ros2 service call /difficulty robot_info_msgs/srv/SetGameDifficulty "{change_difficulty: 'easy'}"
ros2 service call /user_score robot_info_msgs/srv/GetUserScore "{username: 'myuser'}"
```

---

## 9. Communication overview

| Link | Kind | Name | Type | From → To |
|---|---|---|---|---|
| Player data | topic | `/user_information` | `GameUserMsg` | info_user_node → game_node, result_game_node |
| Movement | topic | `/keyboard_control` | `std_msgs/String` | control_node → game_node, (bridge) → info_ros2_node |
| Final score | topic | `/result_information` | `std_msgs/Int64` | game_node → result_game_node |
| Set difficulty | service | `/difficulty` | `SetGameDifficulty` | info_user_node → game_node |
| Get score | service | `/user_score` | `GetUserScore` | result_game_node → game_node |
| Game state | params | `user_name`, `change_player_color`, `screen_param` | str / int / str | stored in game_node |
