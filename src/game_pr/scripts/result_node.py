#!/usr/bin/env python3
import rospy
from std_msgs.msg import Int64
from game_msgs.msg import GameUserMsg

class ResultGameNode(object):
    def __init__(self):
        rospy.init_node('result_game_node')
        self.__username = "Unknown"
        self.__final_score = None

        rospy.Subscriber('/user_information', GameUserMsg, self.__user_info_callback)
        rospy.Subscriber('/result_information', Int64, self.__result_callback)

    def __user_info_callback(self, msg):
        self.__username = msg.username
        rospy.loginfo("Result Node received profile for username: %s", self.__username)

    def __result_callback(self, msg):
        self.__final_score = msg.data
        rospy.loginfo("Result Node received final score: %d", self.__final_score)
        self.display_final_summary()

    def display_final_summary(self):
        print("\n========================================")
        print("          GAME FINAL RESULT             ")
        print("========================================")
        print(f" Player Username : {self.__username}")
        print(f" Final Score     : {self.__final_score}")
        print("========================================\n")

    def run(self):
        rospy.loginfo("Result Game Node running, waiting for results...")
        rospy.spin()

if __name__ == '__main__':
    try:
        node = ResultGameNode()
        node.run()
    except rospy.ROSInterruptException:
        pass