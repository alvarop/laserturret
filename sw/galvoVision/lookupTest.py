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
        getLaserPos(x, y)

def getLaserPos(pixelX, pixelY):
    distTable = []

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

    # Show the four closest calibration points
    # Get the sum of all the distances
    newImg = copy.copy(img)
    dSum = 0.0
    for index in range(4):
        _,_, x, y = dotTable[sortedDistTable[index][0]]
        cv2.circle(newImg, (x, y), 10, [0,255-int(sortedDistTable[index][1]*4),0])
        print x,y, sortedDistTable[index][1]

        dSum += sortedDistTable[index][1]

    print "dSum", dSum

    # Now take the sum of 1/(dist/SUM(distances))
    # Because we want the closest distance to have a higher weight
    idSum = 0.0
    nDist = []
    for index in range(4):
         nDist.append(1/sortedDistTable[index][1])
         print nDist[index]
         idSum += nDist[index]

    newLaserX = 0
    newLaserY = 0
    newX = 0
    newY = 0

    print "idSum", idSum

    # Now compute new x,y position using weighted averages
    for index in range(4):
        dist = sortedDistTable[index][1]
        laserX,laserY, x, y = dotTable[sortedDistTable[index][0]]

        print dist, idSum, nDist[index], (nDist[index]) / idSum # <--- how do we make the shorter one be weighed higher (but sum of all weights add up to 1)?

        # Compute the weighted average of the pixel values (not laser values)
        # just to test the algorithm. We *should* be able to recover the original one
        newX += x * nDist[index] / idSum
        newY += y * nDist[index] / idSum

    newX = int(newX)
    newY = int(newY)
    print newX, newY
    cv2.circle(newImg, (newX, newY), 5, [255,255,255])

    cv2.imshow("image", newImg)

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
