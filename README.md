# ROS1 Robot Factory Game

This repository contains the ROS1 Catkin workspace for Part I of the Robot Programming final assignment. It adapts the Robot Factory game to four independent ROS nodes and one custom message.

## Architecture

| Node | Responsibility | ROS interface |
|---|---|---|
| `info_user_node` | Requests the player's full name, username, and age, then publishes the profile. | Publishes `/user_information` (`game_msgs/GameUserMsg`) |
| `game_node` | Runs the Pygame game, receives profile and movement input, and publishes the final score. | Subscribes to `/user_information` and `/keyboard_control`; publishes `/result_information` (`std_msgs/Int64`) |
| `control_node` | Reads arrow-key or WASD input from its terminal. | Publishes `/keyboard_control` (`std_msgs/String`) |
| `result_node` | Displays the player's username and final score. | Subscribes to `/user_information` and `/result_information` |

The `game_msgs` package defines `GameUserMsg` with `name`, `username`, and `age` fields. The game moves through Welcome, Game, and Final phases.

The workspace includes the supplied `build/` and `devel/` folders and the `GAMEPLAY_ROS.mp4` demonstration. The Catkin folders are generated snapshots and should be rebuilt with `catkin_make` in a local WSL environment. The video is stored with Git LFS; install Git LFS and run `git lfs pull` to retrieve the full recording.

## Requirements

- ROS Noetic on Ubuntu 20.04.
- WSL 2 with WSLg (or another Linux display server) to show the Pygame window from WSL.
- Python 3 and Pygame.
- Git LFS to retrieve the complete demo video.

Install required packages if needed:
bash
sudo apt update
sudo apt install -y python3-pygame git-lfs
git lfs install


The commands below assume ROS Noetic is installed at `/opt/ros/noetic`.

## Open in WSL and VS Code

Clone the `ROS` branch directly as a Catkin workspace in WSL's Linux filesystem:

bash
git clone --branch ROS https://github.com/100523040/RP_AngelPelegry_ErikaSantano_JaimeSole_26.git ~/catkin_ws
cd ~/catkin_ws
code .



## Build

bash
source /opt/ros/noetic/setup.bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash


For each new terminal, run the two `source` commands before starting a node. If Python cannot import Pygame, install it with `python3 -m pip install --user pygame==2.6.1` and rebuild.

## Run the game

Open five WSL terminals. In each one, run:

bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash


Then start one process per terminal in this order:

1. ROS master: `roscore`
2. Result display: `rosrun game_pr result_node.py`
3. Game window: `rosrun game_pr game_node.py`
4. Keyboard controller: `rosrun game_pr control_node.py`
5. Player information prompt: `rosrun game_pr info_user_node.py`

Enter a full name, username, and positive age in Terminal 5. After the welcome screen, move with the arrow keys or W/A/S/D while Terminal 4 has focus. Keep the Pygame window visible to watch the game. At the end, `result_node` prints the username and score. Press Esc in the game window or Ctrl+C in each node terminal to stop; stop `roscore` last.
