#!/usr/bin/python

from cameraReadThread import cameraReadThread
from galvoController import galvoController
import sys
import argparse
import cv2
import math
import serial
import random
import threading
import time
import os
import random
import numpy as np

def constrain(point, lBound, uBound):
    newPoint = []
    for index in range(len(point)):
        if point[index] < lBound:
            newPoint.append(lBound)
        elif point[index] > uBound:
            newPoint.append(uBound)
        else:
            newPoint.append(point[index])

    return tuple(newPoint)

def findDot(image, squareSize, stepSize):
    shape = image.shape
    cols = shape[1]
    rows = shape[0]

    maxRow = 0
    maxCol = 0
    maxVal = 0

    for col in range(0, cols, stepSize):
        for row in range(0, rows, stepSize):
            sumElems = cv2.sumElems(image[row:(row + squareSize), col:(col + squareSize)])[0]
            if sumElems > maxVal:
                maxRow = row
                maxCol = col
                maxVal = sumElems

    return (maxCol, maxRow, maxVal)

def findZeDot(gray, locked = False):
    global oldCols 
    global oldRows
    numCols = gray.shape[1]
    numRows = gray.shape[0]
    if not locked:
        # 
        #  Find general area (200x200px) where dot is
        # 
        squareSize = 200
        maxCol, maxRow, maxVal = findDot(gray, squareSize, squareSize)
        # print "Maximum at: (", maxCol, ",", maxRow, ")"
        # cv2.rectangle(img, (maxCol, maxRow), (maxCol + squareSize, maxRow + squareSize), (0,0,255), 1)

        # 
        # Compute new search area (10% larger in case we caught the dot in an edge)
        # 
        fudge = int(squareSize * 0.1)
        newRows = constrain((maxRow - fudge, maxRow + squareSize + fudge), 0, numRows)
        newCols = constrain((maxCol - fudge, maxCol + squareSize + fudge), 0, numCols)
        cv2.rectangle(img, (newCols[0], newRows[0]), (newCols[1], newRows[1]), (0,0,128), 1)

        squareSize = 50
        maxCol, maxRow, maxVal = findDot(gray, squareSize, squareSize)
        # print "Maximum at: (", maxCol, ",", maxRow, ")"
        # cv2.rectangle(img, (maxCol, maxRow), (maxCol + squareSize, maxRow + squareSize), (0,0,255), 1)

        # 
        # Compute new search area (10% larger in case we caught the dot in an edge)
        # 
        fudge = int(squareSize * 0.1)
        newRows = constrain((maxRow - fudge, maxRow + squareSize + fudge), 0, numRows)
        newCols = constrain((maxCol - fudge, maxCol + squareSize + fudge), 0, numCols)
        cv2.rectangle(img, (newCols[0], newRows[0]), (newCols[1], newRows[1]), (0,128,128), 1)
    else:
        newRows = oldRows
        newCols = oldCols

    # 
    # Narrow down to a 100x1000px area
    # 
    # NOTE: Might want to make this smaller for 720p
    squareSize = 15
    maxCol, maxRow, maxVal = findDot(gray[newRows[0]:newRows[1], newCols[0]:newCols[1]], squareSize, squareSize)
    maxCol += newCols[0]
    maxRow += newRows[0]
    # print "Maximum at: (", maxCol, ",", maxRow, ")"
    # cv2.rectangle(img, (maxCol, maxRow), (maxCol + squareSize, maxRow + squareSize), (0,255,0), 1)

    # 
    # Compute new search area (50% larger in case we caught the dot in an edge)
    # 
    fudge = int(squareSize * 0.5)
    newRows = constrain((maxRow - fudge, maxRow + squareSize + fudge), 0, numRows)
    newCols = constrain((maxCol - fudge, maxCol + squareSize + fudge), 0, numCols)
    # cv2.rectangle(img, (newCols[0], newRows[0]), (newCols[1], newRows[1]), (0,128,0), 1)

    oldCols = newCols
    oldRows = newRows

    # 
    # Narrow down to a 25x25px area and move by 1 pixel for better resolution
    # 
    squareSize = 10
    maxCol, maxRow, maxVal = findDot(gray[newRows[0]:newRows[1], newCols[0]:newCols[1]], squareSize, 1)
    maxCol += newCols[0]
    maxRow += newRows[0]
    # print "Maximum at: (", maxCol, ",", maxRow, ")"
    cv2.rectangle(img, (maxCol, maxRow), (maxCol + squareSize, maxRow + squareSize), (255,255,0), 1)

    return (int(maxCol + squareSize/2),int(maxRow + squareSize/2), maxVal)

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

cam = 1
exposure = 60
scaleFactor = 1080.0/720.0
shooting = False

if len(sys.argv) < 2:
    print 'Usage: ', sys.argv[0], '/path/to/video'
    sys.exit()

oldCols = 0
oldRows = 0

# controller = galvoController(streamFileName, shotDelay= 0.25)
# controller.loadDotTable('dotTable.csv')

cap = cv2.VideoCapture(sys.argv[1])
# Get image margins from dotTable
# No need to display what we can't shoot
# TODO - pass as parameter?
# imgBounds = getPointBounds(controller.dotTable, margin=25)
imgBounds = (0,0,1280,720)

# # Convert image bounds to new coordinate system
# imgBounds = (int(imgBounds[0]/scaleFactor), int(imgBounds[1]/scaleFactor), int(imgBounds[2]/scaleFactor), int(imgBounds[3]/scaleFactor))

# print('New image bounds: (' + str(imgBounds[0]) + ',' +str(imgBounds[1]) + ',' +str(imgBounds[2]) + ',' + str(imgBounds[3]) + ')')

if shooting:
    controller.setLaserState(True)

cv2.namedWindow('img')

lower_blue = np.array([110, 50, 50], dtype=np.uint8)
upper_blue = np.array([130,255,255], dtype=np.uint8)

locked = False
running = True
while cap.isOpened() and running:
    # img = cameraThread.getFrame()
    time.sleep(0.015)
    _, img = cap.read()
    img = cv2.resize(img, (1280, 720)) 
    _, th = cv2.threshold(img, 240, 255, cv2.THRESH_TOZERO)
    # th = cv2.cvtColor(th, cv2.COLOR_BGR2GRAY)
    # _, th = cv2.threshold(th, 10, 255, cv2.THRESH_BINARY)

    th = cv2.cvtColor(th, cv2.COLOR_BGR2HSV)
    th = cv2.inRange(th, lower_blue, upper_blue)

    x,y, maxVal = findZeDot(th, locked)

    x = x + imgBounds[0]
    y = y + imgBounds[1] - 6

    # Only shoot if you think there's something there
    # 100 is completely arbitrary value...
    if maxVal > 100:
        # print maxVal
        cv2.circle(img, (x, y + 6), 5, [0,0,255])
        locked = True
    else:
        locked = False

    if not shooting:
        cv2.imshow('img',img)

    k = cv2.waitKey(1)
    if k == 27:
        running = False

print("Done!")
