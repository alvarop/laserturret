#!/usr/bin/python
# 
# Read in lookup table, wait for mouse click, choose closest point, shoot laser
# Currently using 50x50 lookup table, which takes a while to read in
# 
from galvoController import galvoController
import numpy as np
import threading
import argparse
import math
import time
import cv2
import csv
import sys
import os

laserX = 0
laserY = 0

# Default to 1080p image
imgBounds = (0,0,1920,1080) 

def nothing(x):
    pass

class cameraReadThread(threading.Thread):
    def __init__(self, cam):
        super(cameraReadThread, self).__init__()
        self.cap = cv2.VideoCapture(cam)
        self.cap.set(3, 1920)
        self.cap.set(4, 1080)
        w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print("Resolution: (" + str(int(w)) + "," + str(int(h)) + ")")
        self.running = 1
        self.frameReady = False

    def run(self):
        while self.running:
            _, self.frame = self.cap.read()
            self.frameReady = True

    def getFrame(self):
        while(self.frameReady == False):
            time.sleep(0.001)

        self.frameReady = False
        return self.frame

def getPointBounds(pointList, frame = (0,0,1920,1080), margin = 0):
    minX = frame[2]
    maxX = frame[0]
    minY = frame[3]
    maxY = frame[1]

    for point in pointList:
        x = point[2]
        y = point[3]

        if x > maxX:
            maxX = x
        if x < minX:
            minX = x

        if y > maxY:
            maxY = y
        if y < minY:
            minY = y

    # 
    # Add in margin if necessary
    # 
    minX -= margin
    maxX += margin

    minY -= margin
    maxY += margin    

    # 
    # Make sure we don't go out of bounds
    # 
    if minX < frame[0]:
        minX = frame[0]

    if maxX > frame[2]:
        maxX = frame[2]

    if minY < frame[1]:
        minY = frame[1]

    if maxY > frame[3]:
        maxY = frame[3]

    return (minX, minY, maxX, maxY)

def mouseClick(event, x, y, flags, param):
    global laserX
    global laserY
    global imgBounds
    global controller
    
    if event == cv2.EVENT_LBUTTONDOWN:
        print("Mouse clicked(" + str(x) + ", " + str(y) +")")
        x += imgBounds[0]
        y += imgBounds[1]
        print("Adjusted for frame(" + str(x) + ", " + str(y) +")")
        laserPoint = controller.getLaserPos(x, y)
        laserX = laserPoint[0]
        laserY = laserPoint[1]
        controller.setLaserPos(laserX, laserY)
        time.sleep(0.005)
        controller.laserShoot()

# 
# Start Here!
# 

if len(sys.argv) < 2:
    print 'Usage: ', sys.argv[0], '/path/to/serial/device'
    sys.exit()

streamFileName = sys.argv[1]

controller = galvoController(streamFileName)
controller.loadDotTable('dotTable.csv')

# Get image margins from dotTable
# No need to display what we can't shoot
# TODO - pass as parameter?
imgBounds = getPointBounds(controller.dotTable, margin=25)

print('New image bounds: (' + str(imgBounds[0]) + ',' +str(imgBounds[1]) + ',' +str(imgBounds[2]) + ',' + str(imgBounds[3]) + ')')

cam = 1
cameraThread = cameraReadThread(cam)
cameraThread.daemon = True
cameraThread.start()

os.system("v4l2-ctl -d " + str(cam) + " -c focus_auto=0,exposure_auto=1")
os.system("v4l2-ctl -d " + str(cam) + " -c focus_absolute=0,exposure_absolute=1024")

running = True

cv2.namedWindow("image")
cv2.setMouseCallback("image", mouseClick)
controller.setLaserState(True)
while running:
    image = cameraThread.getFrame()
    # cv2.circle(image, (laserX, laserY), 5, [0,255,0])

    cv2.imshow("image", image[imgBounds[1]:imgBounds[3], imgBounds[0]:imgBounds[2]])
    k = cv2.waitKey(1)
    if k == 27:
        running = False

controller.setLaserState(False)

time.sleep(0.100)
