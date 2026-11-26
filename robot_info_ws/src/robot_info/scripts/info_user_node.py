#!/usr/bin/env python3
"""
INFO_USER_NODE (ROS1)
- Asks the player for name, username and age and publishes them on /user_information
  (robotinfo_msgs/GameUserMsg, latched).
- PART II: asks for the difficulty and calls the /difficulty service
  (robotinfo_msgs/SetGameDifficulty) while game_node is still in phase1.
"""
import rospy
from robotinfo_msgs.msg import GameUserMsg
from robotinfo_msgs.srv import SetGameDifficulty

VALID_DIFFICULTIES = ("easy", "medium", "hard")


class InfoUserNode(object):
    def __init__(self):
        rospy.init_node('info_user_node')
        self.__pub_user_info = rospy.Publisher('/user_information', GameUserMsg, queue_size=10, latch=True)
        self.__name = ""
        self.__username = ""
        self.__age = 0
        self.__difficulty = ""

    def request_user_info(self):
        rospy.loginfo("Requesting player details...")

        while not self.__name.strip():
            self.__name = input("Enter your Full Name: ").strip()

        while not self.__username.strip():
            self.__username = input("Enter your Username: ").strip()

        while True:
            try:
                self.__age = int(input("Enter your Age: "))
                if self.__age > 0:
                    break
                print("Age must be greater than 0.")
            except ValueError:
                print("Please enter a valid number for age.")

        while self.__difficulty not in VALID_DIFFICULTIES:
            answer = input("Choose difficulty [easy/medium/hard] (Enter = medium): ").strip().lower()
            self.__difficulty = answer or "medium"
            if self.__difficulty not in VALID_DIFFICULTIES:
                print("Please type easy, medium or hard.")

    def request_difficulty(self):
        """Service client for /difficulty (only works while the game is in phase1)."""
        try:
            rospy.wait_for_service('/difficulty', timeout=10.0)
            set_difficulty = rospy.ServiceProxy('/difficulty', SetGameDifficulty)
            response = set_difficulty(self.__difficulty)
            if response.success:
                rospy.loginfo("Difficulty set to '%s'.", self.__difficulty)
            else:
                rospy.logwarn("Difficulty NOT changed (game is not in phase1).")
        except rospy.ROSException:
            rospy.logwarn("/difficulty service not available, playing with the default difficulty.")
        except rospy.ServiceException as e:
            rospy.logerr("/difficulty call failed: %s", str(e))

    def publish_info(self):
        msg = GameUserMsg()
        msg.name = self.__name
        msg.username = self.__username
        msg.age = self.__age

        # Wait for subscribers to be ready before publishing
        rospy.sleep(1)
        self.__pub_user_info.publish(msg)
        rospy.loginfo("Published user info: Name='%s', Username='%s', Age=%d", msg.name, msg.username, msg.age)

    def run(self):
        self.request_user_info()
        # Difficulty must be set BEFORE the user info is published: the user info
        # starts the Welcome countdown that moves the game to phase2.
        self.request_difficulty()
        self.publish_info()
        rospy.spin()


if __name__ == '__main__':
    try:
        node = InfoUserNode()
        node.run()
    except rospy.ROSInterruptException:
        pass
