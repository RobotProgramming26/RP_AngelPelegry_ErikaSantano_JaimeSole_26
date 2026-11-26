cmake_minimum_required(VERSION 3.0.2)
project(robot_info)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  robotinfo_msgs
)

catkin_package(
  CATKIN_DEPENDS rospy std_msgs robotinfo_msgs
)

## Install the Python nodes as executables
catkin_install_python(PROGRAMS
  scripts/info_user_node.py
  scripts/game_node.py
  scripts/control_node.py
  scripts/result_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

## Install the launch folder
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
