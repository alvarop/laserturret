#!/usr/bin/python

import sys
import io
import threading
import Queue
import signal
import serial
import time
from datetime import datetime
from random import randint
from libavg import avg
from time import gmtime, strftime

def signal_handler(signal, frame):
    print "exiting"
    sys.exit(0)

class GalleryUI():
    def start(self):
        print "got to UI start."
        self.controller.start()
        self.player.play()

    def run(self):
        #self.controller.run()

        for gallery in self.controller.galleries:
            if gallery.score == self.controller.maxScore:
                self.controller.disableAll(self.controller.currentTarget)
                
                gallery.victoryDance()
                self.controller.done = 1
                self.win_text.text = ("PLAYER %s WINS!" % gallery.id)

                #Want to make it so they no longer match and win condition will stop triggering.
                self.controller.maxScore = -1
            elif self.controller.maxScore == -1:
                pass
            else:
                time_passed = datetime.now() - self.start_time
                timer = round(time_passed.seconds + time_passed.microseconds / 1000000.0, 2)
                self.timer_text.text = str(timer)
 

        #Check for left gallery
        #TODO Don't always assume there are two of these that's dumb.
        self.left_score.text = str(self.controller.galleries[0].score)
        self.right_score.text = str(self.controller.galleries[1].score)



    def __init__(self):
        self.player = avg.Player.get()

        win_x = 1800
        win_y = 1000

        canvas = self.player.createMainCanvas(size=(win_x, win_y))
        rootNode = canvas.getRootNode()
       
        self.left_score = avg.WordsNode(pos=(win_x*.15,10), font="arial", text="-",
                                    parent=rootNode, fontsize=win_y * .6)
        self.right_score = avg.WordsNode(pos=(win_x*.6,10), font="arial", text="-",
                                    parent=rootNode, fontsize=win_y * .6)
        self.win_text = avg.WordsNode(pos=(win_x*.2, win_y*.75), font="arial", text="",
                                    parent=rootNode, fontsize=win_y*.15, color = "ffd700")
        self.timer_text = avg.WordsNode(pos=(win_x*.4,win_y*.9), font="arial", text="",
                                    parent=rootNode, fontsize=win_y*.1)
    
        self.start_time = datetime.now()


        self.controller = GalleryController()
        self.controller.addGallery(sys.argv[1])
        
        # read in a config file
        if len(sys.argv) > 2:
            #self.controller.galleries[0].configFromFile(sys.argv[2].strip())
            self.controller.addGallery(sys.argv[2])

        self.player.setOnFrameHandler(self.run)

class GalleryController():
    def __init__(self):
        self.eventLock = threading.Event() # Used to block main thread while waiting for events
        self.done = 0
        self.currentTarget = 0
        self.galleries = []
        self.maxScore = 2

    def start(self):
        # select first target
        while True:
            self.currentTarget = randint(0, len(self.galleries[0].targets) - 1)
            if self.currentTarget in self.galleries[0].targets:
                break

        self.enableAll(self.currentTarget)

    def run(self):
        startTime = datetime.now()
        '''while not self.done:
            # Wait for next event
            self.eventLock.wait(0.1)
            self.eventLock.clear()
        '''
        self.checkTargets()
        '''endTime = datetime.now()

        totalTime = endTime - startTime

        print "Time: ", (totalTime.seconds + totalTime.microseconds / 1000000.0)
        '''
    def addGallery(self, serialDeviceName):
        galleryIndex = len(self.galleries)
        self.galleries.append(ShootingGallery(serialDeviceName, galleryIndex, self))
        self.galleries[galleryIndex].start()

    #
    # Go through each target and check if they've been hit
    # If they're all hit, exit
    #
    '''    def checkTargets(self):
        for gallery in self.galleries:
            if gallery.score == self.maxScore:
                print "Player ", gallery, "won!"
                self.disableAll(self.currentTarget)
                
                gallery.victoryDance()

                self.done = 1
    '''
        
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
            gallery.targets[id].disable()

    def enableAll(self, id):
        for gallery in self.galleries:
            gallery.targets[id].enable()

class ShootingGallery():
    def __init__(self, streamFileName, id, controller):
        stream = serial.Serial(streamFileName)
        
        self.controller = controller
        self.id = id
        self.started = False
        self.score = 0

        # Start readThread as daemon so it will automatically close on program exit
        self.readThread = serialReadThread(stream, self.id, controller)
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
            self.controller.eventLock.wait(0.1)
            self.controller.eventLock.clear()

        print "gallery started"

    def configFromFile(self, configFile):
        # read in a config file
        config = open(configFile, 'r')
        # read config lines
        for line in config:
            self.writeThread.write(line.strip() + "\n")

    def write(self, command):
        self.writeThread.write(command)

    def victoryDance(self):
        # TODO - make awesomer
        for target in self.targets:
            self.targets[target].enable()
            time.sleep(0.05)
            self.targets[target].disable()

        time.sleep(0.05)

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
    def __init__(self, inStream, id, controller):
        super(serialReadThread, self).__init__()
        self.controller = controller
        self.stream = inStream
        self.running = 1
        self.id = id

    def run(self):
        while self.running:
            try:
                line = self.stream.readline(50);
                if line:
                    self.controller.processLine(line, self.id)
            except serial.SerialException:
                print "serial error"

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
                print line
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


#if len(sys.argv) > 2:
#   controller.addGallery(sys.argv[2])

#controller.start()

ui = GalleryUI()
ui.start()

# Run until done
#controller.run()

sys.exit(0)
