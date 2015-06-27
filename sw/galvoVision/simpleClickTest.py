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
        self.frameCount = 0
        self.running = 1
        self.frameReady = False

    def run(self):
        while self.running:
            _, self.frame = self.cap.read()
            self.frameReady = True
            print self.frameCount
            self.frameCount += 1

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
    if event == cv2.EVENT_LBUTTONDOWN:
        print("Mouse clicked(" + str(x) + ", " + str(y) +")")
        newX, newY = getLaserPos(x, y, 1)
        setLaserPos(newX, newY)
        setLaserState(True)

def getLaserPos(pixelX, pixelY, numSamples = 4):
    distTable = []

    global laserX
    global laserY

    # 
    # Get distance from every calibration point to pixelX, pixelY
    # 
    for index in range(len(dotTable)):
        dotX = dotTable[index][2]
        dotY = dotTable[index][3]
        dist = math.sqrt(math.pow((pixelX - dotX),2) + math.pow((pixelY - dotY),2))
        distTable.append([index, dist])

    # Sort by increasing distance
    sortedDistTable = sorted(distTable, key = lambda x:x[1])

    # Get the closest pixel available and use that as a reference
    # newImg = copy.copy(img)
    newX,newY, x, y = dotTable[sortedDistTable[0][0]]

    # cv2.circle(newImg, (x, y), 5, [0,255,0])
        
    laserX = x
    laserY = y

    return newX, newY
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
with open('testData/dotTable-50x50.csv', 'rb') as csvfile:
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
os.system("v4l2-ctl -d " + str(cam) + " -c focus_absolute=0,exposure_absolute=30")

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
