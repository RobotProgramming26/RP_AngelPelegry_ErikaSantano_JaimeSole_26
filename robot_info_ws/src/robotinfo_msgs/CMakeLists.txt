cmake_minimum_required(VERSION 3.0.2)
project(robotinfo_msgs)

## Message / service generation dependencies
find_package(catkin REQUIRED COMPONENTS
  std_msgs
  message_generation
)

## Custom message (Part I)
add_message_files(
  FILES
  GameUserMsg.msg
)

## Custom services (Part II)
add_service_files(
  FILES
  GetUserScore.srv
  SetGameDifficulty.srv
)

generate_messages(
  DEPENDENCIES
  std_msgs
)

catkin_package(
  CATKIN_DEPENDS std_msgs message_runtime
)
