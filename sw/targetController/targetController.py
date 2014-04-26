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
		self.inStream = io.open(device, 'r')
		self.running = 1
		print "opening ", device
		# TODO - add check in case file couldn't be openend

	def run(self):
		while self.running:
			line = self.inStream.readline();
			inQueueLock.acquire()
			inQueue.put(line)
			inQueueLock.release()

if not len(sys.argv) > 1:
	print "Usage: " + sys.argv[0] + " </dev/serialdevicename>"
	sys.exit(0)

print "Press Ctrl + C to exit"

signal.signal(signal.SIGINT, signal_handler)

inQueueLock = threading.Lock()
inQueue = Queue.Queue()

# Start readThread as daemon so it will automatically close on program exit
readThread = serialReadThread(sys.argv[1])
readThread.daemon = True
readThread.start()

while 1:
	if not inQueue.empty():
		inQueueLock.acquire()
		line = inQueue.get()
		inQueueLock.release()

		# Process line here
		print line

	else:
		# Sleep so CPU doesn't spin at 100%
		# TODO - add nicer blocking
		time.sleep(0.001)
