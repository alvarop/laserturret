#!/usr/bin/python
# 
# Testing calibration procedure for laser/camera system
# 
# Procedure:
# 1. Take photo with no laser (for background subtraction)
# 2. Set laser to positon in grid and turn on
# 3. Take photo of laser
# 4. Find laser dot in image and save position
# 5. Select next point in grid and goto 2.
# 
# With table correlating pixel position with laser setting,
# hopefully we can interpolate to do a reverse search and get
# laser setting from pixel value
# 

from galvoController import galvoController
from cameraReadThread import cameraReadThread
import sys
import argparse
import cv2
import math
import serial
import random
import threading
import time
import os
import numpy as np

def setLaserAndTakePhoto(x, y, cameraThread):
    controller.setLaserState(True)
    controller.setLaserPos(x,y)
    time.sleep(0.1)
    controller.setLaserState(False)
    return cameraThread.getFrame()

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

    return (maxCol, maxRow)

def findZeDot(gray):
    numCols = gray.shape[1]
    numRows = gray.shape[0]

    # 
    #  Find general area (200x200px) where dot is
    # 
    tmpImage = gray
    squareSize = 200
    maxCol, maxRow = findDot(tmpImage, squareSize, squareSize)
    # print "Maximum at: (", maxCol, ",", maxRow, ")"
    # cv2.rectangle(im3, (maxCol, maxRow), (maxCol + squareSize, maxRow + squareSize), (0,0,255), 1)

    # 
    # Compute new search area (10% larger in case we caught the dot in an edge)
    # 
    fudge = int(squareSize * 0.1)
    newRows = constrain((maxRow - fudge, maxRow + squareSize + fudge), 0, numRows)
    newCols = constrain((maxCol - fudge, maxCol + squareSize + fudge), 0, numCols)
    # cv2.rectangle(im3, (newCols[0], newRows[0]), (newCols[1], newRows[1]), (0,0,128), 1)

    # 
    # Narrow down to a 20x20px area
    # 
    tmpImage = gray[newRows[0]:newRows[1], newCols[0]:newCols[1]] # Only needed for profiling
    squareSize = 20
    maxCol, maxRow = findDot(tmpImage, squareSize, squareSize)
    maxCol += newCols[0]
    maxRow += newRows[0]
    # print "Maximum at: (", maxCol, ",", maxRow, ")"
    # cv2.rectangle(im3, (maxCol, maxRow), (maxCol + squareSize, maxRow + squareSize), (0,255,0), 1)

    # 
    # Compute new search area (50% larger in case we caught the dot in an edge)
    # 
    fudge = int(squareSize * 0.5)
    newRows = constrain((maxRow - fudge, maxRow + squareSize + fudge), 0, numRows)
    newCols = constrain((maxCol - fudge, maxCol + squareSize + fudge), 0, numCols)
    # cv2.rectangle(im3, (newCols[0], newRows[0]), (newCols[1], newRows[1]), (0,128,0), 1)

    # 
    # Narrow down to a 5x5px area and move by 1 pixel for better resolution
    # 
    tmpImage = gray[newRows[0]:newRows[1], newCols[0]:newCols[1]] # Only needed for profiling
    squareSize = 5
    maxCol, maxRow = findDot(tmpImage, squareSize, 1)
    maxCol += newCols[0]
    maxRow += newRows[0]
    # print "Maximum at: (", maxCol, ",", maxRow, ")"
    # cv2.rectangle(im3, (maxCol, maxRow), (maxCol + squareSize, maxRow + squareSize), (255,255,0), 1)

    return (int(maxCol + squareSize/2),int(maxRow + squareSize/2))

def getDist(p1, p2):
    return math.sqrt(math.pow((p1[0] - p2[0]),2) + math.pow((p1[1] - p2[1]),2))

def getClosestPoints(pointList, point, nPoints = 4, duplicates = True):
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
        if not duplicates and dotX == pixelX and dotY == pixelY:
            continue

        dist = getDist((pixelX, pixelY), (dotX, dotY))
        # laserDist = getLaserDist((pixelX, pixelY), (dotX, dotY))
        distTable.append([index, dist])    

    sortedDistTable = sorted(distTable, key = lambda x:x[1])

    newTable = []
    for item in sortedDistTable[0:nPoints]:
        newTable.append(pointList[item[0]])
    
    return newTable

def getLaserDist(p1, p2):
    return math.sqrt(math.pow((p1[0] - p2[0]),2) + math.pow((p1[1] - p2[1]),2))

def getPixelDist(p1, p2):
    return math.sqrt(math.pow((p1[2] - p2[2]),2) + math.pow((p1[3] - p2[3]),2))

def getAvgLaserDist(pointList, point, num = 4):
    points = getClosestPoints(pointList, (point[2],point[3]), num, False)
    avgDist = 0.0
    for neighbor in points:
        avgDist += getLaserDist(point, neighbor)

    avgDist /= len(points)

    return avgDist

def getAvgPixelDist(pointList, point, num = 4):
    points = getClosestPoints(pointList, (point[2],point[3]), num, False)
    avgDist = 0.0
    for neighbor in points:
        avgDist += getPixelDist(point, neighbor)

    avgDist /= len(points)

    return avgDist

def removeOutliers(pointList):
    outliers = True
    removedPoints = []

    while outliers:
        laserDistTable = []
        pixelDistTable = []
        magicTable = []
        outlierTable = []

        # Compute average laser distance to 4 closest neighbors
        for point in pointList:
            laserDistTable.append(getAvgLaserDist(pointList, point))
            pixelDistTable.append(getAvgPixelDist(pointList, point))
        
        avgLaserDist = np.mean(laserDistTable)
        avgPixelDist = np.mean(pixelDistTable)
        
        for point in pointList:
            magicTable.append((getAvgLaserDist(pointList, point)/avgLaserDist)/(getAvgPixelDist(pointList, point)/avgPixelDist))

        avgMagicDist = np.mean(magicTable)
        stdMagicDist = np.std(magicTable)
        print "avg = ", avgMagicDist,  "sd = ", stdMagicDist

        if stdMagicDist < 0.25:
            break

        for point in pointList:
            laserDist = getAvgLaserDist(pointList, point)
            pixelDist = getAvgPixelDist(pointList, point)
            magicDist = (laserDist/avgLaserDist)/(pixelDist/avgPixelDist)

            if magicDist > (avgMagicDist + stdMagicDist):
                outlierTable.append([point, magicDist])
                # print point, laserDist/avgLaserDist, pixelDist/avgPixelDist, magicDist

        if len(outlierTable) > 0:
            outliers = True
            sortedOutliers = sorted(outlierTable, key = lambda x:x[1], reverse = True)
            print 'removing', sortedOutliers[0][0]
            removedPoints.append(sortedOutliers[0][0])
            pointList.remove(sortedOutliers[0][0])
        else:
            outliers = False

    return pointList, removedPoints

def mouseEvent(event, x, y, flags, param):
    global height
    global width
    global bounds
    global controller
    
    xPos = int((-x/float(width) + 1) * X_RANGE + X_MIN)
    yPos = int((-y/float(height) + 1) * Y_RANGE + Y_MIN)

    if event == cv2.EVENT_MOUSEMOVE:    
        # print "move", xPos, yPos
        controller.setLaserPos(xPos, yPos)
    elif event == cv2.EVENT_LBUTTONDOWN:
        print "adding bound point", xPos, yPos
        bounds.append([xPos, yPos])

cam = 1
exposure = 25
bounds = []

height = 500
width = 500

MARGIN = 256

# 
# Default values
# 
X_MIN = 0 + MARGIN
X_MAX = 4096 - MARGIN

Y_MIN = 0 + MARGIN
Y_MAX = 4096 - MARGIN

X_RANGE = (X_MAX - X_MIN)
Y_RANGE = (Y_MAX - Y_MIN)

X_CENTER = X_RANGE/ 2.0 + X_MIN
Y_CENTER = Y_RANGE/ 2.0 + Y_MIN

if len(sys.argv) < 2:
    print 'Usage: ', sys.argv[0], '/path/to/serial/device'
    sys.exit()

streamFileName = sys.argv[1]

controller = galvoController(streamFileName)

controller.setLaserPos(X_CENTER, Y_CENTER)
controller.setLaserState(False)

# 
# This lets the use move the laser around by moving the mouse around a window
# By clicking around the area of interest, the calibration can focus inside it
# to provide better resolution
# 
print('Move laser around and click on the boundaries.\nPress ESC to continue')

cv2.namedWindow("trackpad")
cv2.resizeWindow("trackpad", height, height)
cv2.setMouseCallback("trackpad", mouseEvent)
img = np.zeros((height,width,3), np.uint8)
cv2.imshow("trackpad", img)

controller.setLaserState(True)
running = True
while running:  
    k = cv2.waitKey(1)
    if k == 27:
        cv2.destroyWindow("trackpad")
        running = False

controller.setLaserState(False)

# 
# Make sure there's at least one boundary point, then get smallest rectangle
# that encompasses them all
# 
if len(bounds) > 1:
    X_MIN = 1e99
    X_MAX = 0
    Y_MIN = 1e99
    Y_MAX = 0

    for x,y in bounds:
        if x < X_MIN:
            X_MIN = x
        if x > X_MAX:
            X_MAX = x
        if y < Y_MIN:
            Y_MIN = y
        if y > Y_MAX:
            Y_MAX = y

    X_RANGE = (X_MAX - X_MIN)
    Y_RANGE = (Y_MAX - Y_MIN)

    X_CENTER = X_RANGE/ 2.0 + X_MIN
    Y_CENTER = Y_RANGE/ 2.0 + Y_MIN

cameraThread = cameraReadThread(cam)
cameraThread.daemon = True
cameraThread.start()

os.system("v4l2-ctl -d " + str(cam) + " -c focus_auto=0,exposure_auto=1")
os.system("v4l2-ctl -d " + str(cam) + " -c focus_absolute=0,exposure_absolute=" + str(exposure))

controller.setLaserState(False)
time.sleep(0.05)
dark = cameraThread.getFrame()
# cv2.imwrite('dark.png', dark)
time.sleep(0.05)

comb = dark

# Dummy read
setLaserAndTakePhoto(X_CENTER, Y_CENTER, cameraThread)

dotTable = []

random.seed()

for laserYPos in range(Y_MIN, Y_MAX, Y_RANGE/10):
    for laserXPos in range(X_MIN, X_MAX, X_RANGE/10):

        laserY = laserYPos
        laserX = laserXPos

        searching = True
        attempts = 0

        while searching:
            dot = setLaserAndTakePhoto(laserX, laserY, cameraThread)
            diff = cv2.absdiff(dark, dot)

            _, gray = cv2.threshold(diff, 32, 255, cv2.THRESH_TOZERO)
            dotX, dotY = findZeDot(gray)

            # If a dot is 'found' in the top left corner, there's a great chance it's a miss
            if dotX < 10 and dotY < 10:
                print(str(laserX) + "," + str(laserY) + "," + str(dotX) + "," + str(dotY) + " FAIL")

                # Move the laser a little bit and try again
                # How much we move depends on how many retries we've had
                # Usually just re-capturing the image works, but sometimes
                # we have to move it a bit
                laserY = laserYPos + random.randint(-attempts, attempts)
                laserX = laserXPos + random.randint(-attempts, attempts)

                attempts += 1

                # Give up after 5 attempts
                if attempts > 5:
                    print("Giving up")
                    searching = False
                else:
                    print('trying ' + str(laserX) + ',' + str(laserY))
            else:
                print(str(laserX) + "," + str(laserY) + "," + str(dotX) + "," + str(dotY))
                # Only save table data if we found a dot
                dotTable.append([laserX, laserY, dotX, dotY])

                comb = cv2.absdiff(comb, diff)

                searching = False

# 
# Sometimes, the wrong thing is detected. Make sure it's at least close to the points around it
# 
print("Removing outliers")
dotTable, removedTable = removeOutliers(dotTable)
print 'removed ', removedTable
print("Done removing outliers")

# 
# Save calibration data to file
# 
dotFile = open('dotTable.csv', 'w')
for laserX, laserY, dotX, dotY in dotTable:
    dotFile.write(str(laserX) + "," + str(laserY) + "," + str(dotX) + "," + str(dotY) + "\n")
dotFile.close()

# 
# Generate combined image with all calibration points (and detected locations)
# This is useful for debugging
# 
print("Preparing image")
for laserX, laserY, dotX, dotY in dotTable:
    cv2.circle(comb, (dotX, dotY), 5, [0,0,255])

cv2.imwrite('img/comb.png', comb)
print("Done!")

controller.setLaserState(False)
