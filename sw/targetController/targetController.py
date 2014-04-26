#!/usr/bin/python

import sys
import io
import threading
import Queue
import time
import signal

def signal_handler(signal, frame):
	print('You pressed Ctrl+C!')
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
			inQueueLock.acquire()
			inQueue.put(line)
			inQueueLock.release()

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
			else :
				time.sleep(0.001)

	def write(self, line):
		outQueueLock.acquire()
		outQueue.put(line)
		outQueueLock.release()


def processLine(line):
	print line,

# 
#  Start here :D
# 
if not len(sys.argv) > 1:
	print "Usage: " + sys.argv[0] + " </dev/serialdevicename>"
	sys.exit(0)

print "Press Ctrl + C to exit"

signal.signal(signal.SIGINT, signal_handler)

inQueueLock = threading.Lock()
inQueue = Queue.Queue()

outQueueLock = threading.Lock()
outQueue = Queue.Queue()

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

while 1:
	if not inQueue.empty():
		inQueueLock.acquire()
		line = inQueue.get()
		inQueueLock.release()

		# Process line here
		# We could probably do this in the readThread, leaving here for now
		processLine(line)

	else:
		# Sleep so CPU doesn't spin at 100%
		# TODO - add nicer blocking
		time.sleep(0.001)
