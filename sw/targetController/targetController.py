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

class GalleryController():
	def __init__(self):
		self.eventLock = threading.Event() # Used to block main thread while waiting for events
		self.done = 0
		self.currentTarget = 0
		self.galleries = {}
		self.maxScore = 10

	def start(self):
		# select first target
		while True:
			self.currentTarget = randint(0, len(self.galleries[0].targets) - 1)
			if self.currentTarget in self.galleries[0].targets:
				break

		self.enableAll(self.currentTarget)

	def run(self):
		startTime = datetime.now()
		while not self.done:
			# Wait for next event
			self.eventLock.wait(0.1)
			self.eventLock.clear()

			self.checkTargets()

		endTime = datetime.now()

		totalTime = endTime - startTime

		print "Time: ", (totalTime.seconds + totalTime.microseconds / 1000000.0)

	def addGallery(self, serialDeviceName):
		galleryIndex = len(self.galleries)
		self.galleries[galleryIndex] = ShootingGallery(serialDeviceName, galleryIndex)
		self.galleries[galleryIndex].start()

	#
	# Go through each target and check if they've been hit
	# If they're all hit, exit
	#
	def checkTargets(self):
		for gallery in self.galleries:
			if self.galleries[gallery].score == self.maxScore:
				self.done = 1
				print "Player ", gallery, "won!"
				self.disableAll(self.currentTarget)
		
	#
	# Process lines coming from targetController via USB-serial link
	#
	def processLine(self, line, source):
		args = line.split()

		if len(args) > 1:
			if args[1] == "connected":
				targetID = int(args[0])
				print "Target", targetID , "is connected"
				self.galleries[source].targets[targetID] = Target(targetID, self.galleries[source])
				self.galleries[source].targets[targetID].disable()
			elif args[1] == "hit":
				targetID = int(args[0])
				print "Target(", source,")", targetID, "hit!"
				self.galleries[source].score += 1
				if targetID in self.galleries[source].targets:
					self.galleries[source].targets[targetID].hit()
					self.disableAll(targetID)
					while True:
						self.currentTarget = randint(0, len(self.galleries[source].targets) - 1)
						if self.currentTarget in self.galleries[source].targets:
							break 
					self.enableAll(self.currentTarget)
			elif args[1] == "started":
				self.galleries[source].started = True
			else:
				print "controller: ", line,

		# Something happened, let the main thread run
		self.eventLock.set()

	def disableAll(self, id):
		for gallery in self.galleries:
			self.galleries[gallery].targets[id].disable()

	def enableAll(self, id):
		for gallery in self.galleries:
			self.galleries[gallery].targets[id].enable()

class ShootingGallery():
	def __init__(self, streamFileName, id):
		stream = serial.Serial(streamFileName)

		self.id = id
		self.started = False
		self.score = 0

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
			controller.eventLock.wait(0.1)
			controller.eventLock.clear()

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
				controller.processLine(line, self.id)

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
#  Start here :D
# 
if not len(sys.argv) > 1:
	print "Usage: " + sys.argv[0] + " </dev/serialdevicename>"
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print "Press Ctrl + C to exit"

controller = GalleryController()
controller.addGallery(sys.argv[1])

if len(sys.argv) > 2:
	controller.addGallery(sys.argv[2])

controller.start()

# read in a config file
# if len(sys.argv) > 2:
# 	controller.galleries[0].configFromFile(sys.argv[2].strip())

# Run until done
controller.run()

sys.exit(0)
