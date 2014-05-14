#!/usr/bin/python

import sys
import io
import threading
import Queue
import signal
import serial
from datetime import datetime
from random import randint

def signal_handler(signal, frame):
	print "exiting"
	sys.exit(0)

class Target():
	def __init__(self, targetID):
		self.id = targetID
		self.on = False
		self.lock = threading.Lock()

		writeThread.write("set " + str(self.id) + " 0\n")

	def hit(self):
		self.on = False

	def enable(self):
		self.lock.acquire()
		self.on = True
		writeThread.write("set " + str(self.id) + " 1\n")
		self.lock.release()

	def disable(self):
		self.lock.acquire()
		self.on = False
		writeThread.write("set " + str(self.id) + " 0\n")
		self.lock.release()

#
# Read serial stream and add lines to shared queue
#
class serialReadThread(threading.Thread):
	def __init__(self, inStream):
		super(serialReadThread, self).__init__()
		self.stream = inStream
		self.running = 1

	def run(self):
		while self.running:
			line = self.stream.readline(100);
			if line:
				processLine(line, 0)

#
# Write serial stream and add lines to shared queue
#
class serialWriteThread(threading.Thread):
	def __init__(self, outStream):
		super(serialWriteThread, self).__init__()
		self.stream = outStream
		self.running = 1

		self.outQueueLock = threading.Lock()
		self.outQueue = Queue.Queue()
		self.outDataAvailable = threading.Event() # Used to block write thread until data is available

	def run(self):
		while self.running:

			if not self.outQueue.empty():
				self.outQueueLock.acquire()
				line = unicode(self.outQueue.get())
				self.stream.write(str(line))
				self.outQueueLock.release()
			else:
				self.outDataAvailable.wait()
				self.outDataAvailable.clear()

	def write(self, line):
		self.outQueueLock.acquire()
		self.outQueue.put(line)
		self.outQueueLock.release()
		self.outDataAvailable.set()

#
# Process lines coming from targetController via USB-serial link
#
def processLine(line, source):
	global targets
	args = line.split()

	if len(args) > 1:
		if args[1] == "connected":
			targetID = int(args[0])
			print "Target", targetID , "is connected"
			targets[targetID] = Target(targetID)
			targets[targetID].disable()
		elif args[1] == "hit":
			targetID = int(args[0])
			print "Target", targetID, "hit!"
			if targetID in targets:
				targets[targetID].hit()
				while True:
					currentTarget = randint(0, len(targets) - 1)
					if currentTarget in targets:
						break 
				targets[currentTarget].enable()
		elif args[1] == "started":
			while True:
				currentTarget = randint(0, len(targets) - 1)
				if currentTarget in targets:
					break
			targets[currentTarget].enable()
		else:
			print "controller: ", line,

	# Something happened, let the main thread run
	eventLock.set()

#
# Go through each target and check if they've been hit
# If they're all hit, exit
#
def checkTargets():
	if(len(targets) > 0):
		notDone = 0

		for key in targets.keys():
			if targets[key] == True:
				notDone = 1

		if notDone == 0:
			global done
			done = 1
			print "All targets hit!"

# 
#  Start here :D
# 
if not len(sys.argv) > 1:
	print "Usage: " + sys.argv[0] + " </dev/serialdevicename>"
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print "Press Ctrl + C to exit"

eventLock = threading.Event() # Used to block main thread while waiting for events

targets = {}
done = 0
currentTarget = 0
started = False

stream = serial.Serial(sys.argv[1])

# Start readThread as daemon so it will automatically close on program exit
readThread = serialReadThread(stream)
readThread.daemon = True
readThread.start()

# Start writeThread as daemon so it will automatically close on program exit
writeThread = serialWriteThread(stream)
writeThread.daemon = True
writeThread.start()

# Start scan for connected targets
writeThread.write("init\n")

# read in a config file
if len(sys.argv) > 2:
	configFile = sys.argv[2].strip()
	config = open(configFile, 'r')
	# read config lines
	for line in config:
		writeThread.write(line.strip() + "\n")

# Enable targets and wait for hits
writeThread.write("start\n")

while not started:
	eventLock.wait(0.1)
	eventLock.clear()

startTime = datetime.now()

while not done:
	# Wait for next event
	eventLock.wait(0.1)
	eventLock.clear()

	checkTargets()

endTime = datetime.now()

totalTime = endTime - startTime

print "Time: ", (totalTime.seconds + totalTime.microseconds / 1000000.0)

sys.exit(0)
