#!/usr/bin/env python3
import sys
import select
import tty
import termios
import rospy
from std_msgs.msg import String

class ControlNode(object):
    def __init__(self):
        rospy.init_node('control_node')
        self.__pub_control = rospy.Publisher('/keyboard_control', String, queue_size=10)
        self.__settings = termios.tcgetattr(sys.stdin)

    def __get_key(self):
        tty.setraw(sys.stdin.fileno())
        # Reduced timeout from 0.1 to 0.01 for instant key responsiveness
        rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
        if rlist:
            key = sys.stdin.read(1)
            if key == '\x1b': # Escape sequence for arrow keys
                key += sys.stdin.read(2)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.__settings)
        return key

    def run(self):
        rospy.loginfo("Control Node started. Use ARROW KEYS or W/A/S/D to move. Press Ctrl+C to exit.")
        try:
            while not rospy.is_shutdown():
                key = self.__get_key()
                
                # Catch Ctrl+C (\x03) manually because RAW terminal mode intercepts it
                if key == '\x03':
                    rospy.loginfo("Ctrl+C detected. Shutting down Control Node...")
                    break

                command = ""
                if key in ('\x1b[A', 'w', 'W'):
                    command = "UP"
                elif key in ('\x1b[B', 's', 'S'):
                    command = "DOWN"
                elif key in ('\x1b[D', 'a', 'A'):
                    command = "LEFT"
                elif key in ('\x1b[C', 'd', 'D'):
                    command = "RIGHT"

                if command:
                    self.__pub_control.publish(command)
                    rospy.loginfo("Published control command: %s", command)
        except Exception as e:
            rospy.logerr("Error in Control Node: %s", str(e))
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.__settings)

if __name__ == '__main__':
    try:
        node = ControlNode()
        node.run()
    except rospy.ROSInterruptException:
        pass