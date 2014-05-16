#!/usr/bin/python

import sys
import io
import os
import threading
import Queue
import signal
import serial
import time
from datetime import datetime
from random import randint
from libavg import avg
from time import gmtime, strftime
import pyaudio
import wave

CHUNK = 1024

def playRandomSound(soundList):
    playSound(soundList[randint(0, len(soundList) - 1)])

def playSound(filename):
    wf = wave.open(filename, 'rb')

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(CHUNK)

    while data != '':
        stream.write(data)
        data = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()

    p.terminate()

def signal_handler(signal, frame):
    print "exiting"
    sys.exit(0)

class GalleryUI():
    def onMouseDown(self, event):
        self.state = "countdown"
        self.countIndex = 4
        
        for gallery in self.controller.galleries:
            gallery.score = 0

    def start(self):
        print "got to UI start."
        self.player.play()

    def endRun(self):
        self.reset_button.opacity=1
        self.controller.done = 1
        self.win_text.text = ("PLAYER %s WINS!" % self.winner_id)

    def normalRun(self):
        time_passed = datetime.now() - self.start_time
        timer = round(time_passed.seconds + time_passed.microseconds / 1000000.0, 2)
        self.timer_text.text = str(timer)
        
        for gallery in self.controller.galleries:
            if gallery.score == self.controller.maxScore:
                self.controller.disableAll(self.controller.currentTarget)
                
                gallery.victoryDance()
                self.state = "complete"
                
                self.winner_id = gallery.id

        #Check for left gallery
        #TODO Don't always assume there are two of these that's dumb.
        self.left_score.text = str(self.controller.galleries[0].score)
        self.right_score.text = str(self.controller.galleries[1].score)

    def reset_prev_game_visuals(self):
        self.left_score.opacity=0
        self.right_score.opacity=0
        self.reset_button.opacity=0
        self.countdown_text.opacity=1
        self.win_text.opacity=0
        self.timer_text.opacity=0

    def start_scoring_visuals(self):
        self.left_score.opacity=1
        self.right_score.opacity=1
        self.countdown_text.opacity=0
        self.win_text.text=""
        self.win_text.opacity=1
        self.timer_text.opacity=1

    def countDown(self):
        
        self.reset_prev_game_visuals()

        if self.countIndex == 4:
            self.countdown_text.text = "3"
        elif self.countIndex == 3:
            self.countdown_text.text = "2"
            playSound("../sounds/Three.wav")
        elif self.countIndex == 2:
            self.countdown_text.text = "1"
            playSound("../sounds/Two.wav")
        elif self.countIndex == 1:
            playSound("../sounds/One.wav")
        else:
            self.start_scoring_visuals()
            
            self.countdown = False
            self.start_time = datetime.now()
            self.started = True
            self.controller.start()
            self.state = "started"

        self.countIndex -= 1

    def run(self):
        #self.controller.run()

        if self.state == "countdown":
            self.countDown()
        elif self.state == "started":
            self.normalRun()
        else:
            self.endRun()

    def __init__(self):
        self.player = avg.Player.get()

        self.state = "countdown"

        win_x = 1280
        win_y = 800

        canvas = self.player.createMainCanvas(size=(win_x, win_y))
        rootNode = canvas.getRootNode()
       
        self.left_score = avg.WordsNode(pos=(win_x*.15,10), font="arial", text="",
                                    parent=rootNode, fontsize=win_y * .6, opacity=0)
        self.right_score = avg.WordsNode(pos=(win_x*.6,10), font="arial", text="",
                                    parent=rootNode, fontsize=win_y * .6, opacity=0)
        self.win_text = avg.WordsNode(pos=(win_x*.2, win_y*.75), font="arial", text="",
                                    parent=rootNode, fontsize=win_y*.15, color = "ffd700")
        self.timer_text = avg.WordsNode(pos=(win_x*.4,win_y*.9), font="arial", text="",
                                    parent=rootNode, fontsize=win_y*.1)
        self.countdown_text = avg.WordsNode(pos=(win_x*.3,0), font="arial", text="",
                                    parent=rootNode, fontsize=win_y*.9)

        self.reset_button = avg.RectNode(pos=(win_x*.01, win_y*.8), 
                                size=(win_x*.1, win_x*.1), angle=0, parent=rootNode, 
                                opacity=0, fillcolor = "0000FF")
                        
        self.reset_button.connectEventHandler(avg.CURSORDOWN, avg.MOUSE, 
                        self.reset_button, self.onMouseDown)

        self.winner_id = None

        self.start_time = datetime.now()

        self.countdown = True
        self.countIndex = 4

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
        self.maxScore = 10

    def start(self):

        # select first target
        while True:
            self.currentTarget = randint(0, len(self.galleries[0].targets) - 1)
            if self.currentTarget in self.galleries[0].targets:
                break

        self.enableAll(self.currentTarget)

    def run(self):
        self.checkTargets()
    
    def addGallery(self, serialDeviceName):
        galleryIndex = len(self.galleries)
        self.galleries.append(ShootingGallery(serialDeviceName, galleryIndex, self))
        self.galleries[galleryIndex].start()
    
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
                    playRandomSound(laserSounds)

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
        self.write("forceconnect\n")
        
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
                #print line
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

laserSoundPath = "../sounds/laser/"
laserSounds = [laserSoundPath + item for item in os.listdir(laserSoundPath)]

ui = GalleryUI()
ui.start()

# Run until done
#controller.run()

sys.exit(0)
