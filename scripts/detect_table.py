#!/usr/bin/env python

import time

import rospy
from std_msgs.msg import String, Float32MultiArray
from geometry_msgs.msg import Twist

import moveit_commander
import moveit_msgs.msg
from moveit_commander.conversions import pose_to_list

# roslaunch pepper_dcm_bringup pepper_bringup.launch network_interface:=enp2s0 roscore_ip:=kate-iMac.local
# roslaunch naoqi_driver naoqi_driver.launch nao_ip:=192.168.0.139 network_interface:=enp2s0 roscore_ip:=kate-iMac.local
# roslaunch wil_pepper_object_detection moveit_planner.launch
# rosrun find_object_2d find_object_2d image:=/naoqi_driver/camera/front/image_raw

class Error(Exception):
    def __init__(self, error_message):
        self.error_message = error_message
    def ___str__(self):
        return repr(self.error_message)

# spin pepper to detect table
class DetectTable(object):
    def __init__(self):
        # initialise
        rospy.init_node("detect_table", anonymous=True)
        rospy.Subscriber("/objects", Float32MultiArray, self.detect_table)
        # initialise publisher
        # pub_vel = rospy.Publisher('cmd_vel', Twist, queue_size=10)
        # pub_msg = rospy.Publisher('detect/table/result', String, queue_size=10)

        rate = rospy.Rate(10)
        
        rospy.loginfo("Start detecting table")

        # initialise moveit
        super(DetectTable, self).__init__()
        # moveit_commander.roscpp_initialize(sys.argv)
        self.pepper = moveit_commander.RobotCommander()
        self.move_group = moveit_commander.MoveGroupCommander("head")
        self.joint_goal = self.move_group.get_current_joint_values()

        # initialise for object recognition
        # self.finish_one_side = False
        self.at_left = False
        self.at_right = False
        self.at_center = False
        self.detect_object = False
        self.finish_one_side = False
        self.finish_position_check = False
        self.finish_detect = False
        self.left_right_check_count = 4
        self.up_down_check_count = 3
        self.cb_count = 0
        
        while not rospy.is_shutdown():
            if not self.finish_detect:
                self.pitch_check()
            rate.sleep()
        # initialise for turning
        # self.spin_pepper = Twist()
        # self.start_spin = False
        # self.already_spined = False
        # stop_pub_vel = False
        # while not rospy.is_shutdown():
        #     # 1, velocity, when table data is not detect, publish to the velocity
        #     if not self.already_spined:
        #         pub_vel(self.spin_pepper) # check if last message published
        #     elif self.already_spined:
        #         pub_vel(self.spin_pepper)
        #         break
        #     # 2, string, publish when table data detected
        #     pub_msg(self.pub_data)

        #     rate.sleep()

    def pitch_check(self):
        """Move the Pepper's head up and down to detect object"""
        pitch_val = 1.0
        count = 0
        rate = rospy.Rate(10)

        for i in range(3):
            if rospy.is_shutdown():
                break
            if self.finish_detect:
                break
            count = i + 1
            rospy.loginfo("====Start position checking %s ====" % count)
            pitch_val -= 0.5
            self.move_head(0.0, pitch_val)
            time.sleep(2)
            if self.detect_object:
                rospy.loginfo("object detected at joint val => %s" % self.joint_goal)
                self.finish_detect = True
                break
            else:
                self.yaw_check(pitch_val)
            
        if not self.detect_object and not self.finish_one_side:
            rospy.loginfo("====No object in this side, back to initial====")
            self.finish_one_side = True
            self.move_head(0.0, 0.0)
            time.sleep(2)

    def yaw_check(self, pitch_val):
        """Move Pepper's head left and right to detect object"""
        right = False
        val = 0.0
        change_yaw_val = 0.5
        for i in range(4):
            if rospy.is_shutdown():
                break
            if self.detect_object:
                rospy.loginfo("object detected at joint val => %s" % self.joint_goal)
                self.finish_detect = True
                break
            else:
                if right:
                    change_yaw_val = -0.5
                cr = i + 1
                rospy.loginfo("====Start side checking %s ====" % cr)
                val += change_yaw_val
                self.move_head(val, pitch_val)
                if val == 1.0:
                    right = True
    
    def move_head(self, yaw_val, pitch_val):
        """ Set joints value for move the head of Pepper
        Argument:
            yaw_val: float value for yaw joint (move left or right)
            pitch_val: float value for pitch joint (move up or down)
        """
        if (-0.6 <= pitch_val <= 0.6) and (-1.5 <= yaw_val <= 1.5):
            self.joint_goal[0] = yaw_val
            self.joint_goal[1] = pitch_val # move down
            self.execute_joint_goal()
            # when at 0.5, the max left and right are 1 , -1
            # rospy.loginfo(move_group.get_current_state())
            rospy.loginfo("moved to => %s" % self.joint_goal)
            rospy.loginfo("Sleep for 3 sec")
            time.sleep(3)
        else:
            raise Error("Joint value out of range")

    def execute_joint_goal(self):
        """ Execute joint value to let Pepper move its head """
        self.move_group.go(self.joint_goal, wait=True)
        self.move_group.stop()


    def turning_pepper(self, val):
        # after spin when one side no table object detect, change one side detect to false
        if self.detected_table:
            self.spin_pepper.angular.z = val
            self.start_spin = True
        elif objects.data[0] == 1:
            self.spin_pepper.angular.z = 0.0
            if self.start_spin:
                self.already_spined = True

    def detect_table(self, objects):
        if len(objects.data) > 0 and objects.data[0] == 2:
            self.detect_object = True
        else:
            self.detect_object = False
        
        
        
        # more
        # check if the object width and height is in relation to the real frame
        # if is in relation to the real frame
        # spin the pepper, until the object is in the ejge of the camera

if __name__ == '__main__':
    detect = DetectTable()

    