#!/usr/bin/env python
# thanks to http://stackoverflow.com/questions/11918999/key-listeners-in-python
import sys
import serial
import threading
import pygame, sys, time
from pygame.locals import *

posX = 0
posY = 0
laserOn = 0

pygame.init()
pygame.joystick.init()
controller = pygame.joystick.Joystick(0)
controller.init()
screen = pygame.display.set_mode((400,300))
pygame.display.set_caption('protoxController')

interval = 0.05

xAxis = 2
yAxis = 3

r1Button = 11
psButton = 16

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

# 
# Convert -1.0 to 1.0 controller input to a 8 bit integer value 
# 
def getAxes():
	x = int(controller.get_axis(xAxis) * 4000)
	y = int(controller.get_axis(yAxis) * -2500)

	return [x, y]

def setPos(x, y):
	stream.write('m 1 ' + str(x) + '\n')
	print('m 1 ' + str(x) + '\n')
	stream.write('m 0 ' + str(y) + '\n')
	print('m 0 ' + str(y) + '\n')

def center():
	global posX
	global posY
	stream.write('m center\n')
	posX = 0
	posY = 0

def setLaser(laserState):
	global laserOn
	if laserState == True:
		stream.write('laser 1\n')
	else:
		stream.write('laser 0\n')

if len(sys.argv) < 2:
	print 'Usage: ', sys.argv[0], '/path/to/serial/device'
	sys.exit()

streamFileName = sys.argv[1]

stream = serial.Serial(streamFileName)

# Start readThread as daemon so it will automatically close on program exit
readThread = serialReadThread(stream)
readThread.daemon = True
readThread.start()

center()

print ''
print 'Use the right stick to move the turret.'
print 'Press the R1 for some laser acction!'
print ''
print 'exit with Esc or PS button'
print ''

# 
# Main control loop
# 
loopQuit = False
laserOn = False

setLaser(False)

while loopQuit == False:

	[x, y] = getAxes()

	setPos(x, y)

	# print('remote ' + str(x) + ' ' + str(y) + '\n')
	# stream.write('remote ' + str(throttle) + ' ' + str(pitch) + ' ' + str(yaw) + ' ' + str(roll) + ' ' + '\n')
	
	if controller.get_button(r1Button) == 1 and laserOn == False:
		laserOn = True
		setLaser(True)
	elif controller.get_button(r1Button) == 0 and laserOn == True:
		laserOn = False
		setLaser(False)

	if controller.get_button(psButton) == 1:
		loopQuit = True
		setLaser(False)

	for event in pygame.event.get():
		if event.type == QUIT:
			loopQuit = True
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				loopQuit = True

	# pygame.display.update()
	time.sleep(interval)

pygame.quit()
sys.exit()
