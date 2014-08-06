'''Webcams learn to detect blue circles, take two.'''

import SimpleCV as scv
import sys
import threading
import serial
import Queue

from math import sqrt
from random import randrange

STATE = 'idle'

#CONTROLFILE = io.open(ARGS.serial, mode='wt')
CONTROLFILE = '/dev/ttyACM0'
#CONTROLFILE = '/dev/pts/5'

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

def centering():
    pass
def idle():
    pass
def seeking_target():
    pass
def shooting():
    pass
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
        self.writeThread.write("m clear\n")
         
    def main(self):

        global STATE       
 
        display = scv.Display(resolution=(1024, 768))
        cam = scv.Camera(1, {"height": 768, "width": 1024})
        normalDisplay = True
       
        #State dictionary
        states = {'centering': centering, 'idle': idle, 
                'seeking_trg': seeking_target, 'shooting': shooting,
                'victory!': victory_dance
                }

 
        while display.isNotDone():
            img = cam.getImage()
            #img = cam.getImage().flipHorizontal()

            if display.mouseRight:
                break
            if display.mouseLeft:
                normalDisplay = not(normalDisplay)

            segmented = img.colorDistance(scv.Color.WHITE).dilate(2).binarize(25)
            #segmented = np.where(segmented < 200, 0, segmented)
            blobs = segmented.findBlobs(minsize=200, maxsize=7000)
            circles = filter(lambda b: b.isCircle(0.4), blobs) if blobs else None

            states[STATE]() 
        

            if normalDisplay:
                img.show()
            else:
                segmented.show()

controller = turretController(CONTROLFILE)
controller.main()
