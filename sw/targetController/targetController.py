#!/usr/bin/python

import sys
import io
import threading
import time

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
			print line,

readThread = serialReadThread("/dev/cu.usbmodem1421")

readThread.start()

time.sleep(10)

print "exiting"
readThread.running = 0

