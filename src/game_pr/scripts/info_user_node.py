#!/usr/bin/env python3
import rospy
from game_msgs.msg import GameUserMsg

class InfoUserNode(object):
    def __init__(self):
        rospy.init_node('info_user_node')
        self.__pub_user_info = rospy.Publisher('/user_information', GameUserMsg, queue_size=10, latch=True)
        self.__name = ""
        self.__username = ""
        self.__age = 0

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
        self.publish_info()
        rospy.spin()

if __name__ == '__main__':
    try:
        node = InfoUserNode()
        node.run()
    except rospy.ROSInterruptException:
        pass