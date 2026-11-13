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

## Requirements

- ROS Noetic on Ubuntu 20.04.
- WSL 2 with WSLg (or another Linux display server) to show the Pygame window from WSL.
- Python 3 and Pygame.

Install Pygame if needed:

```bash
sudo apt update
sudo apt install -y python3-pygame
```

The commands below assume ROS Noetic is installed at `/opt/ros/noetic`.

## Open in WSL and VS Code

Clone the `ROS` branch directly as a Catkin workspace in WSL's Linux filesystem:

```bash
git clone --branch ROS https://github.com/100523040/RP_AngelPelegry_ErikaSantano_JaimeSole_26.git ~/catkin_ws
cd ~/catkin_ws
code .
```

If `code .` does not open a WSL window, install/enable the Microsoft WSL extension in VS Code and reopen the folder in WSL.

## Build

```bash
source /opt/ros/noetic/setup.bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

For each new terminal, run the two `source` commands before starting a node. If Python cannot import Pygame, install it with `sudo apt install -y python3-pygame` and rebuild.

## Run the game

Open five WSL terminals. In each one, run:

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
```

Then start one process per terminal in this order:

1. ROS master: `roscore`
2. Result display: `rosrun game_pr result_node.py`
3. Game window: `rosrun game_pr game_node.py`
4. Keyboard controller: `rosrun game_pr control_node.py`
5. Player information prompt: `rosrun game_pr info_user_node.py`

Enter a full name, username, and positive age in Terminal 5. After the welcome screen, move with the arrow keys or W/A/S/D while Terminal 4 has focus. Keep the Pygame window visible to watch the game. At the end, `result_node` prints the username and score. Press Esc in the game window or Ctrl+C in each node terminal to stop; stop `roscore` last.

## Record a demonstration

On Windows, open Xbox Game Bar with **Win+G** and start/stop recording with **Win+Alt+R**. Show the game window and the result terminal, including player details, gameplay, and final score. Recordings are saved in **Videos/Captures** by default.

## Publish changes to ROS

To publish commits to the `ROS` branch without merging them into `main`:

```bash
git switch ROS
git status --short
git add README.md .gitignore src
git commit -m "Add ROS1 game workspace and run instructions"
git push origin ROS
```

A push updates the `ROS` branch only; it does not merge it into `main`. Do not open or merge a pull request unless the team asks for one. Generated Catkin folders (`build`, `devel`, `install`, and `logs`) are ignored and should not be committed.
