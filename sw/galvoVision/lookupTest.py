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
    newImg = copy.copy(img)
    for index in range(4):
        _,_, x, y = dotTable[sortedDistTable[index][0]]
        cv2.circle(newImg, (x, y), 10, [0,255,0])
        print x,y

    cv2.imshow("image", newImg)

# 
# Start Here!
# 

# 
# Read table into list of lists (i think)
# Format is "laserX, laserY, pixelX, pixelY"
# 
with open('dotTable.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        dotTable.append([int(row[0]), int(row[1]), int(row[2]), int(row[3])])

# 
# Load calibration image for visual feedback during testing
# 
img = cv2.imread("comb.png")
cv2.namedWindow("image")
cv2.setMouseCallback("image", mouseClick)
cv2.imshow("image", img)

cv2.waitKey()
