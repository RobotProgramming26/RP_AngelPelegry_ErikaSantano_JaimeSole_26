#!/usr/bin/env python3
"""
INFO_ROS2_NODE (ROS2)  -  file robot_info2_node.py, package robot_info2

Listener that receives, through ros1_bridge, the std_msgs/String messages that the
ROS1 control_node publishes on /keyboard_control (UP, DOWN, LEFT, RIGHT).

EXTRA (optional): if the ROS2 package robot_info_msgs is built and the bridge was
compiled from source with it, it also listens to /user_information (GameUserMsg).
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

try:  # EXTRA part: only available if robot_info_msgs (ROS2) is built
    from robot_info_msgs.msg import GameUserMsg
except ImportError:
    GameUserMsg = None


class InfoRos2Node(Node):
    def __init__(self):
        super().__init__('info_ros2_node')
        self.__counts = {"UP": 0, "DOWN": 0, "LEFT": 0, "RIGHT": 0}

        self.__sub_control = self.create_subscription(
            String, '/keyboard_control', self.__keyboard_callback, 10)
        self.get_logger().info("info_ros2_node listening to /keyboard_control (bridged from ROS1)")

        if GameUserMsg is not None:
            self.__sub_user = self.create_subscription(
                GameUserMsg, '/user_information', self.__user_callback, 10)
            self.get_logger().info("EXTRA: also listening to /user_information (GameUserMsg)")

    def __keyboard_callback(self, msg):
        command = msg.data
        if command in self.__counts:
            self.__counts[command] += 1
        self.get_logger().info(
            f"Received command: {command}  | totals: " +
            ", ".join(f"{k}={v}" for k, v in self.__counts.items()))

    def __user_callback(self, msg):
        self.get_logger().info(
            f"Received player: name='{msg.name}', username='{msg.username}', age={msg.age}")


def main(args=None):
    rclpy.init(args=args)
    node = InfoRos2Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
