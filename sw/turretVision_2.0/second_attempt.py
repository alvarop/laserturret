'''Webcams learn to detect blue circles, take two.'''

import SimpleCV as scv
import cv2
import sys
import threading
import serial
import Queue
import numpy as np
import time 

from math import sqrt
from random import randrange

STATE = 'idle'

FEEDBACK = []
CONTROLFILE = '/dev/ttyACM0'

x_off, y_off = 0, 0
msTime = lambda: int(round(time.time() * 1000))

time_allowed = msTime()
justShot = False

def nothing(x):
    pass

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
            try:
                line = self.stream.readline(50)
                if line:
                    FEEDBACK.append(line)
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

def shooting(self, turn_on):

    if turn_on:
        self.writeThread.write("laser 1\n")
        print "Firing"
    else:
        self.writeThread.write("laser 0\n")
        print "Not firing."

def centering(args):
    global x_off, y_off
    global time_allowed
    global justShot

    self = args['self']
    print "Now centering on a target."
    
    screen_x, screen_y = args['s_x'], args['s_y']
    closest_trg = args['closest']
    trg_x, trg_y, trg_r = closest_trg.x, closest_trg.y, closest_trg.radius()

    x_center = screen_x/2 + x_off
    y_center = screen_y/2 + y_off

    if msTime() > time_allowed:
        #If we're within the bounds of the target, KILL.
        dist_frm_center = sqrt((trg_x-x_center)**2 + (trg_y-y_center)**2)
        print "Dist is %s and r is %s" % (dist_frm_center, trg_r)
        if dist_frm_center <= trg_r and not justShot:    
            shooting(self, True)
            time_allowed = msTime() + 500
            justShot = True
        else:
            shooting(self, False)
            if justShot:
                justShot = False      
                time_allowed = msTime() + 1500

    if closest_trg.radius() > 2:
        args['seg'].dl().circle((trg_x, trg_y), closest_trg.radius(), scv.Color.RED, width=2)

    x_offset = trg_x - x_center
    y_offset = trg_y - y_center 
    print "Our trg is at : %s, %s" % (trg_x, trg_y)    
    print "Offsets at : %s, %s" % (x_offset, y_offset)    
 
    x_delta = x_offset * .5
    #The motor moves negatve when given positive, and pos when given negative.
    y_delta = -y_offset * .5
 
    args['t_x'] += x_delta    
    args['t_y'] += y_delta    
    print "Our turret should be at : %s, %s" % (args['t_x'], args['t_y'])    
  
    #Position that we're sending it to is now "relative" to where we think
    #it is. Can adjust after.
    self.writeThread.write("\n")
    self.writeThread.write("m 0 %s\n" % args['t_x'])
    self.writeThread.write("\n")
    self.writeThread.write("m 1 %s\n" % args['t_y'])

    #Redetect the closest circle.
    seeking_target(args)
 
    pass
def idle(args):
    pass
def seeking_target(args):
    global STATE

    print "Now seeking a target!"
 
    circles = args['circles']
    if circles:
            
        #Closest circle to the center of the image
        closest_circle = circles.sortDistance()
        print "Closest circles are: %s" % list(closest_circle)
        closest_circle = closest_circle[0]
        args['closest'] = closest_circle

        STATE = 'centering'
    else:
        STATE = 'seeking_trg'
        if 'closest' in args:
            del args['closest']

def victory_dance():
    pass


class turretController():
    
    def __init__(self, control_file):

        stream = serial.Serial(control_file)

        # Start readThread as daemon so it will automatically close on program exit
        self.readThread = serialReadThread(stream)
        self.readThread.daemon = True
        self.readThread.start()
        
        # Start writeThread as daemon so it will automatically close on program exit
        self.writeThread = serialWriteThread(stream)
        self.writeThread.daemon = True
        self.writeThread.start()

        self.writeThread.write("\n")
        self.writeThread.write("m center\n")
         
    def main(self):

        global STATE
        global x_off, y_off

        blankimg = np.zeros([300, 512, 3], np.uint8)

        cv2.namedWindow('sliders')
        cv2.createTrackbar('Hue', 'sliders', 105, 180, nothing)
        cv2.createTrackbar('x', 'sliders', 127, 300, nothing)
        cv2.createTrackbar('y', 'sliders', 194, 300, nothing)
        # cv2.createTrackbar('Saturation', 'sliders', 100, 255, nothing) 
        # cv2.createTrackbar('Value', 'sliders', 100, 255, nothing) 
        # cv2.createTrackbar('Diff', 'sliders', 0, 50, nothing) 

        screen_x, screen_y = 1024, 768 
        display = scv.Display(resolution=(screen_x, screen_y))
        cam = scv.Camera(0, {"height": 768, "width": 1024})
        normalDisplay = True
        turret_x, turret_y = 0, 0    
   
        #State dictionary
        states = {'centering': centering, 'idle': idle, 
                'seeking_trg': seeking_target, 'victory!': victory_dance
                }
        #Dictionary of arguments that will be passed to each state.
        args = {'t_x': turret_x, 't_y': turret_y, 
                's_x': screen_x, 's_y': screen_y,
                'self': self}
 
        while display.isNotDone():

            hue = cv2.getTrackbarPos('Hue', 'sliders')
            x_off = cv2.getTrackbarPos('x', 'sliders') - 150
            y_off = cv2.getTrackbarPos('y', 'sliders') - 150

            img = cam.getImage()
            #segmented = img.colorDistance(scv.Color.WHITE).dilate(2).binarize(25)
            segmented = img.hueDistance(hue, minsaturation=40, minvalue=40).binarize(50)
            # segmented = img.hueDistance(hue, minsaturation=40, minvalue=40).invert()
            args['img'] = img
            args['seg'] = segmented

            #segmented = np.where(segmented < 200, 0, segmented)
            blobs = segmented.findBlobs(minsize=10, maxsize=7000)
            if blobs:
                circles = blobs.filter([b.isCircle(0.5) for b in blobs])
                args['circles'] = circles
            else:
                args['circles'] = []   
 
            print "Switch to %s" % STATE 
            states[STATE](args)
            
            if display.mouseLeft and \
                (display.mouseX < 50 and display.mouseY < 50):
                STATE = 'seeking_trg'
                print "Chg to seeking." 
            if display.mouseRight:
                break
            if display.mouseLeft:
                normalDisplay = not(normalDisplay)
        
            #Determines which type of picture is shown.
            if normalDisplay:
                img.show()
                cv2.imshow('sliders', blankimg)
                cv2.waitKey(1)
            else:
                segmented.show()
                cv2.imshow('sliders', blankimg)
                cv2.waitKey(1)

controller = turretController(CONTROLFILE)
controller.main()
