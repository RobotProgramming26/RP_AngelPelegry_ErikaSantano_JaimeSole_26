#!/usr/bin/env python3
"""
RESULT_GAME_NODE (ROS1)
- Subscribes to /user_information (GameUserMsg) and /result_information (Int64).
- PART II: service client of /user_score (robotinfo_msgs/GetUserScore). When the final
  score arrives it sends the username and prints the percentage returned by game_node.
"""
import rospy
from std_msgs.msg import Int64
from robotinfo_msgs.msg import GameUserMsg
from robotinfo_msgs.srv import GetUserScore


class ResultGameNode(object):
    def __init__(self):
        rospy.init_node('result_game_node')
        self.__username = "Unknown"
        self.__final_score = None
        self.__score_percent = None

        rospy.Subscriber('/user_information', GameUserMsg, self.__user_info_callback)
        rospy.Subscriber('/result_information', Int64, self.__result_callback)

        # Service client (proxy created once, reused on every call)
        self.__user_score_client = rospy.ServiceProxy('/user_score', GetUserScore)

    def __user_info_callback(self, msg):
        self.__username = msg.username
        rospy.loginfo("Result Node received profile for username: %s", self.__username)

    def __result_callback(self, msg):
        self.__final_score = msg.data
        rospy.loginfo("Result Node received final score: %d", self.__final_score)
        self.request_score_percentage()
        self.display_final_summary()

    def request_score_percentage(self):
        try:
            rospy.wait_for_service('/user_score', timeout=5.0)
            response = self.__user_score_client(self.__username)
            self.__score_percent = response.score
            if response.score < 0:
                rospy.logwarn("/user_score: game_node does not know user '%s'", self.__username)
            else:
                rospy.loginfo("/user_score: '%s' obtained %d%% of the maximum score",
                              self.__username, response.score)
        except (rospy.ROSException, rospy.ServiceException) as e:
            rospy.logerr("Could not call /user_score: %s", str(e))

    def display_final_summary(self):
        if self.__score_percent is None or self.__score_percent < 0:
            percent = "N/A"
        else:
            percent = f"{self.__score_percent} %"
        print("\n========================================")
        print("          GAME FINAL RESULT             ")
        print("========================================")
        print(f" Player Username : {self.__username}")
        print(f" Final Score     : {self.__final_score}")
        print(f" Score Percentage: {percent}")
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
