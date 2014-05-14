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

class ShootingGallery():
	def __init__(self, streamFileName, id):
		stream = serial.Serial(streamFileName)

		self.id = id
		self.started = False

		# Start readThread as daemon so it will automatically close on program exit
		self.readThread = serialReadThread(stream, self.id)
		self.readThread.daemon = True
		self.readThread.start()

		# Start writeThread as daemon so it will automatically close on program exit
		self.writeThread = serialWriteThread(stream)
		self.writeThread.daemon = True
		self.writeThread.start()

		self.targets = {}

	def start(self):
		print "starting gallery", str(self.id)

		# Start scan for connected targets
		self.write("init\n")

		# Enable targets and wait for hits
		self.write("start\n")

		while not self.started:
			eventLock.wait(0.1)
			eventLock.clear()

		print "gallery started"

	def configFromFile(self, configFile):
		# read in a config file
		config = open(configFile, 'r')
		# read config lines
		for line in config:
			self.writeThread.write(line.strip() + "\n")

	def write(self, command):
		self.writeThread.write(command)

class Target(object):
	def __init__(self, targetID, gallery):
		self.id = targetID
		self.on = False
		self.lock = threading.Lock()
		self.gallery = gallery

		self.gallery.write("set " + str(self.id) + " 0\n")

	def hit(self):
		self.on = False

	def enable(self):
		self.lock.acquire()
		self.on = True
		self.gallery.write("set " + str(self.id) + " 1\n")
		self.lock.release()

	def disable(self):
		self.lock.acquire()
		self.on = False
		self.gallery.write("set " + str(self.id) + " 0\n")
		self.lock.release()

#
# Read serial stream and add lines to shared queue
#
class serialReadThread(threading.Thread):
	def __init__(self, inStream, id):
		super(serialReadThread, self).__init__()
		self.stream = inStream
		self.running = 1
		self.id = id

	def run(self):
		while self.running:
			line = self.stream.readline(100);
			if line:
				processLine(line, self.id)

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
	args = line.split()

	if len(args) > 1:
		if args[1] == "connected":
			targetID = int(args[0])
			print "Target", targetID , "is connected"
			galleries[source].targets[targetID] = Target(targetID, galleries[source])
			galleries[source].targets[targetID].disable()
		elif args[1] == "hit":
			targetID = int(args[0])
			print "Target", targetID, "hit!"
			if targetID in galleries[source].targets:
				galleries[source].targets[targetID].hit()
				while True:
					currentTarget = randint(0, len(galleries[source].targets) - 1)
					if currentTarget in galleries[source].targets:
						break 
				galleries[source].targets[currentTarget].enable()
		elif args[1] == "started":
			galleries[source].started = True
			while True:
				currentTarget = randint(0, len(galleries[source].targets) - 1)
				if currentTarget in galleries[source].targets:
					break
			galleries[source].targets[currentTarget].enable()
		else:
			print "controller: ", line,

	# Something happened, let the main thread run
	eventLock.set()

#
# Go through each target and check if they've been hit
# If they're all hit, exit
#
def checkTargets():
	if(len(galleries[0].targets) > 0):
		notDone = 0

		for key in galleries[0].targets.keys():
			if galleries[0].targets[key].on == True:
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

done = 0
currentTarget = 0

galleries = {}
galleries[0] = ShootingGallery(sys.argv[1], 0)
galleries[0].start()

# read in a config file
if len(sys.argv) > 2:
	galleries[0].configFromFile(sys.argv[2].strip())

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
