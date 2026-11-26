cmake_minimum_required(VERSION 3.8)
project(robot_info_msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Same definitions as the ROS1 package robotinfo_msgs
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/GameUserMsg.msg"
  "srv/GetUserScore.srv"
  "srv/SetGameDifficulty.srv"
)

# ros1_bridge reads this file to pair robotinfo_msgs (ROS1) <-> robot_info_msgs (ROS2)
install(FILES mapping_rules.yaml
  DESTINATION share/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
