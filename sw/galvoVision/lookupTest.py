#!/usr/bin/python
# 
# Read in lookup table and *hopefully* figure out how to do
# a reverse lookup (pixel to laser pos)
# 
import argparse
import cv2
import numpy as np
import math
import timeit
import csv
import copy

dotTable = []

def nothing(x):
    pass

def mouseClick(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print("Mouse clicked(" + str(x) + ", " + str(y) +")")
        newImg = copy.copy(img)
        laserPoint = getLaserPos(x, y, newImg)

        print laserPoint

        cv2.imshow("image", newImg)

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
    drawPoints(points, img, 5, [0,128,0])

    # Interpolate between them to get new mid-points (with mid laser values calculated too)
    points = addMidPoints(points, img)
    drawPoints(points, img, 3, [0,128,0])

    # Repeat with the new list (including virtual points)
    points = getClosestPoints(points, (pixelX, pixelY), 4)
    drawPoints(points, img, 3, [0,0,128])

    # Add more virtual points!
    points = addMidPoints(points, img)
    drawPoints(points, img, 2, [0,0,128])

    # And again...
    points = getClosestPoints(points, (pixelX, pixelY), 4)
    drawPoints(points, img, 2, [0,128,128])

    points = addMidPoints(points, img, dupeThreshold = 4)
    drawPoints(points, img, 1, [0,128,128])

    # and again
    points = getClosestPoints(points, (pixelX, pixelY), 4)
    drawPoints(points, img, 1, [0,255,0])

    points = addMidPoints(points, img, dupeThreshold = 2)
    drawPoints(points, img, 1, [0,255,0])

    # Get final closest point
    points = getClosestPoints(points, (pixelX, pixelY), 1)
    return points[0]

# 
# Start Here!
# 

# 
# Read table into list of lists (i think)
# Format is "laserX, laserY, pixelX, pixelY"
# 
with open('testData/dotTable.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        dotTable.append([int(row[0]), int(row[1]), int(row[2]), int(row[3])])

# 
# Load calibration image for visual feedback during testing
# 
img = cv2.imread("testData/comb.png")
cv2.namedWindow("image")
cv2.setMouseCallback("image", mouseClick)
cv2.imshow("image", img)

cv2.waitKey()
