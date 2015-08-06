#!/usr/bin/env python
#

import serial
import threading
import math
import sys
import time

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

if len(sys.argv) < 2:
	print 'Usage: ', sys.argv[0], '/path/to/serial/device'
	sys.exit()

streamFileName = sys.argv[1]

stream = serial.Serial(streamFileName)

# Start readThread as daemon so it will automatically close on program exit
readThread = serialReadThread(stream)
readThread.daemon = True
readThread.start()

connecting = True

stream.write('laser 1\n')


MARGIN = 256
X_MIN = 0 + MARGIN
X_MAX = 4096 - MARGIN
X_RANGE = (X_MAX - X_MIN)

Y_MIN = 0 + MARGIN
Y_MAX = 4096 - MARGIN
Y_RANGE = (Y_MAX - Y_MIN)

X_CENTER = X_RANGE/ 2.0 + X_MIN
Y_CENTER = Y_RANGE/ 2.0 + Y_MIN

MAX_RANGE = 200
ADC_RANGE = 256

def drawCrircle(xCenter,yCenter,radius):
	xPos = -math.sin(0) * radius + xCenter
	yPos = math.cos(0) * radius + yCenter

	stream.write('laser 1\n')
	stream.write('g 0 ' + str(int(xPos)) + '\n' + 'g 1 ' + str(int(yPos)) + '\n')
	time.sleep(0.001)
	stream.write('laser 0\n')

	for x in range(MAX_RANGE):
		xPos = -math.sin(x * math.pi * 2.0 / MAX_RANGE) * radius + xCenter
		yPos = math.cos(x * math.pi * 2.0 / MAX_RANGE) * radius + yCenter
		stream.write('g 0 ' + str(int(xPos)) + '\n' + 'g 1 ' + str(int(yPos)) + '\n')
		time.sleep(0.001)

	stream.write('laser 1\n')

# time.sleep(10)

# for dummy in range(50):
# 	drawCrircle(X_CENTER, Y_CENTER, 100)
# 	drawCrircle(X_CENTER + X_RANGE/4, Y_CENTER + Y_RANGE/4, 100)
# 	drawCrircle(X_CENTER - X_RANGE/4, Y_CENTER + Y_RANGE/4, 100)
# 	drawCrircle(X_CENTER + X_RANGE/4, Y_CENTER - Y_RANGE/4, 100)
# 	drawCrircle(X_CENTER - X_RANGE/4, Y_CENTER - Y_RANGE/4, 100)

# Circle
stream.write('laser 1\n')
for x in range(MAX_RANGE * 10):
	xPos = -math.sin(x * math.pi * 2.0 / MAX_RANGE) * X_RANGE/2 + X_CENTER
	yPos = math.cos(x * math.pi * 2.0 / MAX_RANGE) * Y_RANGE/2 + Y_CENTER
	stream.write('g 0 ' + str(int(xPos)) + '\n' + 'g 1 ' + str(int(yPos)) + '\n')
	time.sleep(0.002)
stream.write('laser 0\n')

# Grid
# for x in range(X_MIN, X_MAX + X_RANGE/10, X_RANGE/10):
# 	xPos = x
# 	yPos = Y_MIN
# 	stream.write('laser 1\n')
# 	stream.write('g 0 ' + str(int(xPos)) + '\n' + 'g 1 ' + str(int(yPos)) + '\n')
# 	time.sleep(0.002)
# 	stream.write('laser 0\n')
# 	for y in range(Y_MIN, Y_MAX, 1):
# 		yPos = y
# 		stream.write('g 1 ' + str(int(yPos)) + '\n')
# 		time.sleep(0.001)
# stream.write('laser 1\n')

# for y in range(Y_MIN, Y_MAX + Y_RANGE/10, Y_RANGE/10):
# 	xPos = X_MIN
# 	yPos = y
# 	stream.write('laser 1\n')
# 	stream.write('g 0 ' + str(int(xPos)) + '\n' + 'g 1 ' + str(int(yPos)) + '\n')
# 	time.sleep(0.002)
# 	stream.write('laser 0\n')
# 	for x in range(X_MIN, X_MAX, 1):
# 		xPos = x
# 		stream.write('g 0 ' + str(int(xPos)) + '\n')
# 		time.sleep(0.001)
# stream.write('laser 1\n')

