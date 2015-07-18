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

def setLaserAndTakePhoto(x, y):
    setLaserState(True)
    setLaserPos(x,y)
    time.sleep(0.1)
    setLaserState(False)
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
            pointList.remove(sortedOutliers[0][0])
        else:
            outliers = False

    return pointList

cam = 1
exposure = 25

MARGIN = 256
X_MIN = 0 + MARGIN
X_MAX = 4096 - MARGIN
X_RANGE = (X_MAX - X_MIN)

Y_MIN = 0 + MARGIN
Y_MAX = 4096 - MARGIN
Y_RANGE = (Y_MAX - Y_MIN)

X_CENTER = X_RANGE/ 2.0 + X_MIN
Y_CENTER = Y_RANGE/ 2.0 + Y_MIN

if len(sys.argv) < 2:
    print 'Usage: ', sys.argv[0], '/path/to/serial/device'
    sys.exit()

streamFileName = sys.argv[1]

stream = serial.Serial(streamFileName)

# Start readThread as daemon so it will automatically close on program exit
readThread = serialReadThread(stream)
readThread.daemon = True
readThread.start()

setLaserPos(X_CENTER, Y_CENTER)
setLaserState(False)

cameraThread = cameraReadThread(cam)
cameraThread.daemon = True
cameraThread.start()

os.system("v4l2-ctl -d " + str(cam) + " -c focus_auto=0,exposure_auto=1")
os.system("v4l2-ctl -d " + str(cam) + " -c focus_absolute=0,exposure_absolute=" + str(exposure))

setLaserState(False)
time.sleep(0.05)
dark = cameraThread.getFrame()
# cv2.imwrite('dark.png', dark)
time.sleep(0.05)

comb = dark

# Dummy read
setLaserAndTakePhoto(X_CENTER, Y_CENTER)

dotTable = []

random.seed()

for laserYPos in range(Y_MIN, Y_MAX, Y_RANGE/10):
    for laserXPos in range(X_MIN, X_MAX, X_RANGE/10):

        laserY = laserYPos
        laserX = laserXPos

        searching = True
        attempts = 0

        while searching:
            dot = setLaserAndTakePhoto(laserX, laserY)
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

print("Removing outliers")
dotTable = removeOutliers(dotTable)
print("Done removing outliers")

dotFile = open('dotTable.csv', 'w')
for laserX, laserY, dotX, dotY in dotTable:
    dotFile.write(str(laserX) + "," + str(laserY) + "," + str(dotX) + "," + str(dotY) + "\n")
dotFile.close()

print("Preparing image")
for laserX, laserY, dotX, dotY in dotTable:
    cv2.circle(comb, (dotX, dotY), 5, [0,0,255])

cv2.imwrite('img/comb.png', comb)
print("Done!")

setLaserState(False)
