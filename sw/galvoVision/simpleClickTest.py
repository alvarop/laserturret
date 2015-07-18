#!/usr/bin/python
# 
# Read in lookup table, wait for mouse click, choose closest point, shoot laser
# Currently using 50x50 lookup table, which takes a while to read in
# 
import argparse
import cv2
import numpy as np
import math
import serial
import threading
import timeit
import csv
import time
import copy
import os
import sys

dotTable = []
laserX = 0
laserY = 0

def nothing(x):
    pass

class serialReadThread(threading.Thread):
    def __init__(self, inStream):
        super(serialReadThread, self).__init__()
        self.stream = inStream
        self.running = 1

    def run(self):
        while self.running:
            try:
                line = self.stream.readline(50)
                if line:
                    print line
            except serial.SerialException:
                print "serial error"

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


def setLaserState(state):
    if(state):
        stream.write('laser 0\n')
    else:
        stream.write('laser 1\n')

def setLaserPos(x, y):
    stream.write("g 0 " + str(x) + "\n")
    stream.write("g 1 " + str(y) + "\n")

def mouseClick(event, x, y, flags, param):
    global laserX
    global laserY

    if event == cv2.EVENT_LBUTTONDOWN:
        print("Mouse clicked(" + str(x) + ", " + str(y) +")")
        laserPoint = getLaserPos(x, y, 1)
        laserX = laserPoint[0]
        laserY = laserPoint[1]
        setLaserPos(laserX, laserY)
        setLaserState(True)

def drawPoints(pointList, img, size = 1, color = [0, 255, 0]):
    for point in pointList:
        matchingPoint = (point[2], point[3])
        cv2.circle(img, matchingPoint, size, color)

def addMidPoints(pointList, img, dupeThreshold = 5):
    newPointList = copy.copy(pointList)
    for p1 in pointList:
        for p2 in pointList:
            
            # Remove complete duplicates
            if p1 == p2:
                continue

            midPoint = getMidPoint((p1[2], p1[3]), (p2[2], p2[3]))
            midLaserPoint = getMidPoint((p1[0], p1[1]), (p2[0], p2[1]))
            
            # Check against all other points, if they are within dupeThreshold, don't add the new one
            dist = 1e99
            for p3 in newPointList:
                 dist = getDist((midPoint[0], midPoint[1]), (p3[2], p3[3]))
                 if dist < dupeThreshold:
                    break

            # This is a new point, add it!
            if dist >= dupeThreshold:
                newPointList.append([midLaserPoint[0], midLaserPoint[1], midPoint[0], midPoint[1]])

    return newPointList

def getMidPoint(p1, p2):
    return int((p1[0] + p2[0])/2), int((p1[1] + p2[1])/2)

def getDist(p1, p2):
    return math.sqrt(math.pow((p1[0] - p2[0]),2) + math.pow((p1[1] - p2[1]),2))

def getClosestPoints(pointList, point, nPoints = 4):
    distTable = []

    pixelX = point[0]
    pixelY = point[1]

    # 
    # Get distance from every calibration point to pixelX, pixelY
    # 
    for index in range(len(pointList)):
        dotX = pointList[index][2]
        dotY = pointList[index][3]

        # Don't include if it's an exact match
        # if dotX == pixelX and dotY == pixelY:
            # continue

        dist = getDist((pixelX, pixelY), (dotX, dotY))
        distTable.append([index, dist])    

    sortedDistTable = sorted(distTable, key = lambda x:x[1])

    newTable = []
    for item in sortedDistTable[0:nPoints]:
        newTable.append(pointList[item[0]])
    
    return newTable

def getLaserPos(pixelX, pixelY, img = None):
    # Get the four closest points
    points = getClosestPoints(dotTable, (pixelX, pixelY), 4)
    # drawPoints(points, img, 5, [0,128,0])

    # Interpolate between them to get new mid-points (with mid laser values calculated too)
    points = addMidPoints(points, img)
    # drawPoints(points, img, 3, [0,128,0])

    # Repeat with the new list (including virtual points)
    points = getClosestPoints(points, (pixelX, pixelY), 4)
    # drawPoints(points, img, 3, [0,0,128])

    # Add more virtual points!
    points = addMidPoints(points, img)
    # drawPoints(points, img, 2, [0,0,128])

    # And again...
    points = getClosestPoints(points, (pixelX, pixelY), 4)
    # drawPoints(points, img, 2, [0,128,128])

    points = addMidPoints(points, img, dupeThreshold = 4)
    # drawPoints(points, img, 1, [0,128,128])

    # and again
    points = getClosestPoints(points, (pixelX, pixelY), 4)
    # drawPoints(points, img, 1, [0,255,0])

    points = addMidPoints(points, img, dupeThreshold = 2)
    # drawPoints(points, img, 1, [0,255,0])

    # Get final closest point
    points = getClosestPoints(points, (pixelX, pixelY), 1)
    return points[0]


# 
# Start Here!
# 

if len(sys.argv) < 2:
    print 'Usage: ', sys.argv[0], '/path/to/serial/device'
    sys.exit()

streamFileName = sys.argv[1]

stream = serial.Serial(streamFileName)

# Start readThread as daemon so it will automatically close on program exit
readThread = serialReadThread(stream)
readThread.daemon = True
readThread.start()

# 
# Read table into list of lists (i think)
# Format is "laserX, laserY, pixelX, pixelY"
# 
with open('dotTable.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        # Ignore bad values
        if int(row[2]) > 0 and int(row[3]) > 0:
            dotTable.append([int(row[0]), int(row[1]), int(row[2]), int(row[3])])

cam = 0
cameraThread = cameraReadThread(cam)
cameraThread.daemon = True
cameraThread.start()

os.system("v4l2-ctl -d " + str(cam) + " -c focus_auto=0,exposure_auto=1")
os.system("v4l2-ctl -d " + str(cam) + " -c focus_absolute=0,exposure_absolute=1024")

running = True

cv2.namedWindow("image")
cv2.setMouseCallback("image", mouseClick)
setLaserState(False)
while running:
    image = cameraThread.getFrame()
    cv2.circle(image, (laserX, laserY), 5, [0,255,0])
    # TODO - only show relevant part of the picture here
    # will have to adjust mouse, but if we can't shoot it, why even look at it!?
    cv2.imshow("image", image)
    k = cv2.waitKey(1)
    if k == 27:
        running = False

setLaserState(False)

time.sleep(0.100)
