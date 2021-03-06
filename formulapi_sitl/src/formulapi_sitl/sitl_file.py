#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import roslib
roslib.load_manifest('formulapi_sitl')
import sys
import traceback
import rospy
import cv2
import numpy
import math
import logging
import socket
import threading
import time
import datetime
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Twist
from formulapi_source import ImageProcessor

class formulapi_sim(object):
    def __init__(self):
      self.imgprocess = ImageProcessor.ImageProcessor()
      self.bridge = CvBridge()
      self.latestimage = None
      self.process = False
            
      """ROS Subscriptions """
      self.image_pub = rospy.Publisher("/image_converter/output_video",Image, queue_size=10)
      self.image_sub = rospy.Subscriber("/cam/camera_/image_raw",Image,self.cvt_image)
      self.cmdVelocityPub = rospy.Publisher('/platform_control/cmd_vel', Twist, queue_size=10)

      self.targetlane = 0
      self.cmdvel = Twist()
      self.last_time = rospy.Time()
      self.sim_time = rospy.Time()
      self.dt = 0
      self.position_er = 0
      self.position_er_last = 0;
      self.cp = 0
      self.vel_er = 0
      self.cd = 0
      self.Kp = 3
      self.Kd = 3.5
      
    def limit(self, input, min, max):
	if input < min:
		input = min
	if input > max:
		input = max
	return input

    def AdjustMotorSpeed(self, pos):

	self.cmdvel.linear.x = 0.2

	self.sim_time = rospy.Time.now()
	self.dt = (self.sim_time - self.last_time).to_sec();

	self.position_er = self.targetlane - pos
	self.cp = self.position_er * self.Kp 
	self.vel_er = (self.position_er - self.position_er_last) * self.dt
	self.cd = self.vel_er * self.Kd

	self.cmdvel.angular.z = self.cp - self.cd
	self.cmdvel.angular.z = self.limit(self.cmdvel.angular.z, -1, 1)
	self.cmdVelocityPub.publish(self.cmdvel)

	self.position_er_last = self.position_er
	self.last_time = self.sim_time

    def cvt_image(self,data):  
      try:
        self.latestimage = self.bridge.imgmsg_to_cv2(data, "bgr8")	
      except CvBridgeError as e:
        print(e)
      if self.process != True:
          self.process = True    

    def run(self):

      while True:
	
	# Only run loop if we have an image
	if self.process:

      	    self.imgprocess.ProcessingImage(self.latestimage)	# FormulaPi Image Processing Function

            self.AdjustMotorSpeed(self.imgprocess.trackoffset)	# Compute Motor Commands From Image Output

	    # Publish Processed Image
	    cvImage = self.imgprocess.outputImage
	    try:
	    	imgmsg = self.bridge.cv2_to_imgmsg(cvImage, "bgr8")
	    	self.image_pub.publish(imgmsg)
	    except CvBridgeError as e:
            	print(e)
	    
            #cv2.imshow("Image window", self.cvImage)
            #cv2.waitKey(3)

def main(args):

  rospy.init_node('formulapi_sitl', anonymous=True)

  sim = formulapi_sim() 

  sim.run() 


  try:
    rospy.spin()
  except KeyboardInterrupt:
    print("Shutting down")
  cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)
