#!/usr/bin/env python

import rospy
from std_msgs.msg import String, Float32MultiArray
from geometry_msgs.msg import Twist

import time
import numpy
import cv2

class TurningPepper(object):
    """ Turning Pepper towards object """
    def __init__(self):
        """ Initialise class, and looping the code untill shutdown the node """
        # initialise
        rospy.init_node("turning_pepper", anonymous=True)
        rospy.Subscriber("/objects", Float32MultiArray, self.get_object_center)
        rospy.Subscriber('detect_table_result', String, self.get_direction)
        # initialise publisher
        self.pub_vel = rospy.Publisher('cmd_vel', Twist, queue_size=10)
        pub_msg = rospy.Publisher('approach_table', String, queue_size=10)
        # initialise for determine the center of the object
        self.object_center = None
        self.go_right = False
        self.go_left = False
        self.detect_object = False
        self.ready_to_spin = False
        # initialise for turning the pepper
        self.spin_pepper = Twist()
        self.approach = False
        rate = rospy.Rate(10)
        # start node with call back functions and publish new topics
        while not rospy.is_shutdown():
            if self.ready_to_spin:
                if not self.approach:
                    self.turning_pepper()
                elif self.approach:
                    pub_msg.publish("ready")
            rate.sleep()

    def get_object_center(self, objects):
        """ Detect the coordinate for the center of the object """
        if len(objects.data) > 0 and objects.data[0] == 1:
            self.detect_object = True
            # get transformation matrix
            matrix = numpy.zeros((3, 3), dtype='float32')
            matrix[0, 0] = objects.data[3]
            matrix[1, 0] = objects.data[4]
            matrix[2, 0] = objects.data[5]
            matrix[0, 1] = objects.data[6]
            matrix[1, 1] = objects.data[7]
            matrix[2, 1] = objects.data[8]
            matrix[0, 2] = objects.data[9]
            matrix[1, 2] = objects.data[10]
            matrix[2, 2] = objects.data[11]
            
            # get array of 2d vectors to transform
            width = objects.data[1]
            height = objects.data[2]
            inpt_array = numpy.float32([[0,0],[width-1,0],[0,height-1],[width-1,height-1]]).reshape(-1,1,2)
            
            # perfrom perspective transformation
            outpt_array = cv2.perspectiveTransform(inpt_array, matrix)
            
            # get object center
            self.object_center = (outpt_array[0, 0] + outpt_array[1, 0] + outpt_array[2, 0] + outpt_array[3, 0]) / 4

    def get_direction(self, msg):
        """ Determine the object is at which side of pepper """
        if len(msg.data) > 0:
            self.ready_to_spin = True
        if msg.data == "right":
            self.go_right = True
        elif msg.data == "left":
            self.go_left = True
    
    def turning_pepper(self):
        """ Truning pepper untill the object center (x-axis) is at the frame center (x-axis) """
        if self.detect_object and 158 < self.object_center[0] < 162:
            # if the object center is at frame center, then stop turning
            self.spin_pepper.angular.z = 0.0
            self.pub_vel.publish(self.spin_pepper)
            time.sleep(5) # publish message only for 5 seconds
            self.approach = True
        elif self.go_right:
            self.spin_pepper.angular.z = -0.1
            self.pub_vel.publish(self.spin_pepper)
        elif self.go_left:
            self.spin_pepper.angular.z = 0.1
            self.pub_vel.publish(self.spin_pepper)

if __name__ == "__main__":
    start = TurningPepper()