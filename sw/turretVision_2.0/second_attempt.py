'''Webcams learn to detect blue circles, take two.'''

import SimpleCV as scv
import sys
import threading
import serial
import Queue

from math import sqrt
from random import randrange

STATE = 'idle'

FEEDBACK = []
CONTROLFILE = '/dev/ttyACM0'

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

    self = args['self']
    print "Now centering on a target."
    
    screen_x, screen_y = args['s_x'], args['s_y']
    closest_trg = args['closest']
    trg_x, trg_y, trg_r = closest_trg.x, closest_trg.y, closest_trg.radius()

    #If we're within the bounds of the target, KILL.
    dist_frm_center = sqrt((trg_x-screen_x/2)**2 + (trg_y-screen_y/2)**2)
    print "Dist is %s and r is %s" % (dist_frm_center, trg_r)
    if dist_frm_center <= trg_r:    
        shooting(self, True)
    else:
        shooting(self, False)       

    args['seg'].dl().circle((trg_x, trg_y), closest_trg.radius(), scv.Color.RED, width=4)

    x_offset = trg_x - screen_x/2
    y_offset = trg_y - screen_y/2 
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

        screen_x, screen_y = 1024, 768 
        display = scv.Display(resolution=(screen_x, screen_y))
        cam = scv.Camera(1, {"height": 768, "width": 1024})
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
            img = cam.getImage()
            segmented = img.colorDistance(scv.Color.WHITE).dilate(2).binarize(25)
            args['img'] = img
            args['seg'] = segmented

            #segmented = np.where(segmented < 200, 0, segmented)
            blobs = segmented.findBlobs(minsize=100, maxsize=7000)
            if blobs:
                circles = blobs.filter([b.isCircle(0.3) for b in blobs])
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
            else:
                segmented.show()

controller = turretController(CONTROLFILE)
controller.main()
