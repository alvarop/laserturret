#!/usr/bin/env python
# thanks to http://stackoverflow.com/questions/11918999/key-listeners-in-python
import sys
import termios
import contextlib
import serial
import threading

left = 0x61
right = 0x64
up = 0x77
down = 0x73
enter = 0x0A
space = 0x20

posX = 0
posY = 0
laserOn = 0

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

def moveRight():
	global posX
	posX = posX + 50
	stream.write('m 0 ' + str(posX) + '\n')
	print('m 0 ' + str(posX) + '\n')

def moveLeft():
	global posX
	posX = posX - 50
	stream.write('m 0 ' + str(posX) + '\n')
	print('m 0 ' + str(posX) + '\n')	

def moveUp():
	global posY
	posY = posY + 50
	stream.write('m 1 ' + str(posY) + '\n')
	print('m 1 ' + str(posY) + '\n')

def moveDown():
	global posY
	posY = posY - 50
	stream.write('m 1 ' + str(posY) + '\n')
	print('m 1 ' + str(posY) + '\n')	

def center():
	global posX
	global posY
	stream.write('m center\n')
	posX = 0
	posY = 0

def toggleLaser():
	global laserOn
	laserOn = laserOn ^ 1
	stream.write('laser ' + str(laserOn) + '\n')

fns = {}

fns[right] = moveRight
fns[left] = moveLeft

fns[up] = moveUp
fns[down] = moveDown

fns[enter] = center
fns[space] = toggleLaser

@contextlib.contextmanager
def raw_mode(file):
	old_attrs = termios.tcgetattr(file.fileno())
	new_attrs = old_attrs[:]
	new_attrs[3] = new_attrs[3] & ~(termios.ECHO | termios.ICANON)
	try:
		termios.tcsetattr(file.fileno(), termios.TCSADRAIN, new_attrs)
		yield
	finally:
		termios.tcsetattr(file.fileno(), termios.TCSADRAIN, old_attrs)

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

# stream.write('m dbgon\n')

print ''
print 'Use WASD to move the turret.'
print 'Press enter to set the new origin (center)'
print 'Press the spacebar for some laser acction!'
print ''
print 'exit with ^C or ^D'
print ''
with raw_mode(sys.stdin):
	try:
		while True:
			ch = sys.stdin.read(1)
			if not ch or ch == chr(4):
				break
			
			if ord(ch) in fns:
				fns[ord(ch)]()
			else:
				print "Unknown key:", ord(ch)


	except (KeyboardInterrupt, EOFError):
		pass

stream.write('m dbgoff\n')
