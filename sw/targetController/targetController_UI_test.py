#!/usr/bin/python

import sys
import io
import threading
import Queue
import signal
from datetime import datetime
from random import randint
from libavg import avg

player = avg.Player.get()
canvas = player.createMainCanvas(size=(640, 480))
rootNode = canvas.getRootNode()
SCORE = 0

#I realize that I have no clue if this system is set up for a single set of targets
#or multiple. If there's a separate dictionary of target items, can update the player
#score too.
def change_score():
    comp_score.text = str(SCORE)

comp_score = avg.WordsNode(pos=(50,50), font="arial", text="0",
    parent=rootNode, fontsize=120)
player_score = avg.WordsNode(pos=(300,50), font="arial", text="0",
    parent=rootNode, fontsize=120)
player.setOnFrameHandler(change_score)

player.play()

def signal_handler(signal, frame):
	print "exiting"
	sys.exit(0)

#
# Read serial stream and add lines to shared queue
#
class serialReadThread(threading.Thread):
	def __init__(self,device):
		super(serialReadThread, self).__init__()
		self.stream = io.open(device, 'r')
		self.running = 1
		print "opening ", device
		# TODO - add check in case file couldn't be openend

	def run(self):
		while self.running:
			line = self.stream.readline();
			processLine(line)

#
# Write serial stream and add lines to shared queue
#
class serialWriteThread(threading.Thread):
	def __init__(self,device):
		super(serialWriteThread, self).__init__()
		self.stream = io.open(device, 'w')
		self.running = 1
		print "opening ", device
		# TODO - add check in case file couldn't be openend

	def run(self):
		while self.running:

			if not outQueue.empty():
				outQueueLock.acquire()
				line = unicode(outQueue.get())
				self.stream.write(line)
				outQueueLock.release()
			else:
				outDataAvailable.wait()
				outDataAvailable.clear()

	def write(self, line):
		outQueueLock.acquire()
		outQueue.put(line)
		outQueueLock.release()
		outDataAvailable.set()

#
# Process lines coming from targetController via USB-serial link
#
def processLine(line):
	global targets
	args = line.split()

	if len(args) > 1:
		if args[1] == "connected":
			targetID = int(args[0])
			print "Target", targetID , "is connected"
			targetLock.acquire()
			targets[targetID] = True
			targetLock.release()
			writeThread.write("set " + str(targetID) + " 0\n")
		elif args[1] == "hit":
			targetID = int(args[0])
			print "Target", targetID, "hit!"
			
            #Adding 1 to our hit counter
            SCORE += 1

            if targetID in targets:
				targetLock.acquire()
				targets[targetID] = False
				while True:
					currentTarget = randint(0, len(targets) - 1)
					if currentTarget in targets:
						break 
				targets[currentTarget] = True
				targetLock.release()
				writeThread.write("set " + str(currentTarget) + " 1\n")
		elif args[1] == "started":
			while True:
					currentTarget = randint(0, len(targets) - 1)
					if currentTarget in targets:
						break 
			writeThread.write("set " + str(currentTarget) + " 1\n")
			targetLock.acquire()
			targets[currentTarget] = True
			targetLock.release()

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

		targetLock.acquire()
		for key in targets.keys():
			if targets[key] == True:
				notDone = 1
		targetLock.release()

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

outQueueLock = threading.Lock()
outQueue = Queue.Queue()

outDataAvailable = threading.Event() # Used to block write thread until data is available

targetLock = threading.Lock()

eventLock = threading.Event() # Used to block main thread while waiting for events

targets = {}
done = 0
currentTarget = 0

# Start readThread as daemon so it will automatically close on program exit
readThread = serialReadThread(sys.argv[1])
readThread.daemon = True
readThread.start()

# Start writeThread as daemon so it will automatically close on program exit
writeThread = serialWriteThread(sys.argv[1])
writeThread.daemon = True
writeThread.start()

# Start scan for connected targets
writeThread.write("init\n")

# Enable targets and wait for hits
writeThread.write("start\n")

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
