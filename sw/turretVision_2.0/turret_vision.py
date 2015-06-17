'''Webcams learn to detect blue circles, take two.'''

import SimpleCV as scv
import sys
import threading
import serial
import Queue

from math import sqrt
from random import randrange

display = scv.Display(resolution=(1024, 768))
cam = scv.Camera(1, {"height": 768, "width": 1024})
normalDisplay = True

PREV_COORDS = [(0, 0, 0)]
MOVE_RIGHT = True
MOVE_DOWN = True
LOCK_TIMER, LOCK_AMT = 0, 100
ALPHA_CIRCLE = None
FEEDBACK = []
SEEK_LIST = [(340, 340), (680, 340), (680, 680), (340, 680)]
RE_SEEK = True

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

def find_shortest_distances(curr):
    '''Naively assume that for a single coord, shortest distance
    will be a 1-to-1 for all in both curr set and prev set.
    curr- [(x, y, radius), (x2, y2, radius), ...]'''
    master_set = []
   
    #Don't need the radius for now. 
    for x,y,r in curr:
        best_dist = sys.maxint
        best_pair = None    

        for p_x, p_y, _ in PREV_COORDS:
            dist = sqrt((x-p_x)**2 + (y-p_y)**2)
            
            if dist < best_dist: 
                best_dist = dist
                best_pair = p_x, p_y
        #Associate current x,y to optimal distance pair
        #Pass along radius for later use. This the the r of the current. Assume
        #it will be closer to future size than previous.
        master_set.append([best_pair, (x,y), r])
    
    return master_set

def anticipate_the_future(matched_pairs):
    '''matched pairs- list of x, y coordinate pairs, and the radius of most
    recent circle.'''
    print "Matched: %s" % matched_pairs
    future_locs = []

    #Coord set- [(x1, y1), (x2, y2), radius2]
    for coord_set in matched_pairs:
    
        first_x, first_y = coord_set[0]
        sec_x, sec_y = coord_set[1]
        r = coord_set[2]

        new_x = first_x + 2 * (sec_x-first_x)
        new_y = first_y + 2 * (sec_y-first_y)

        print("C_X:%s, C_Y:%s, F_X:%s, F_Y:%s" % (sec_x, sec_y, new_x, new_y))          
        future_locs.append([(sec_x,sec_y), (new_x, new_y), r])
    
    #Future locs- [[(x_cur, y_cur), (x_fut, y_fut), r_cur], ...]
    return future_locs 

def determine_alpha_circle(future_locs, frm_cir_coords):
    '''future_locs- Of the form 
        [[(curr_x, curr_y), (future_x, future_y), curr_radius],
         [...], [...]]
    '''

    hits_others = True

    #Assuming we have circles, want to pick the one which
    #is at the front. Defined as "future direction doesn't
    #run into any others.
    for moving_circles in future_locs:
        current_x, current_y = moving_circles[0]
        future_x, future_y = moving_circles[1] 
        radius = moving_circles[2]               
    
        #For the moment, ignoring the radius of the current circle it's
        #comparing against.
        for curr_x, curr_y, _ in frm_cir_coords:
            
            #If we're looking at ourself.
            if (curr_x, curr_y) == (current_x, current_y):
                continue             

            in_x_bounds = future_x-radius < curr_x < future_x + radius
            in_y_bounds = future_y - radius < curr_x < future_y + radius              
            if not in_x_bounds and not in_y_bounds:
                alpha_circle = moving_circles
                hits_others = False
    
    if hits_others:
        alpha_circle = future_locs[0] 

    return alpha_circle

def seek_state(self, x, y):
    global MOVE_RIGHT, MOVE_LEFT
    print "I AM IN SEEK STATE. Sending to (%s, %s)" % (x, y)
    
    self.writeThread.write("\n")
    self.writeThread.write("m 0 %s\n" % x)
    self.writeThread.write("\n")
    self.writeThread.write("m 1 %s\n" % y)

def get_turret_xy(self):

    #get x, translate it to our coordinate system
    #Will write the x coords back
    self.writeThread.write("m 0 \n")

    timeout = 5000000
    while not FEEDBACK and timeout > 0:
        timeout -= 1
        continue 
    if FEEDBACK:       
        try:
            #At beginning, turret doesn't always know where it is.
            line = FEEDBACK.pop()
            print "Line reads: %s" % line
            _, _, turret_x = line.split(" ")
            turret_x = int(turret_x.rstrip("\n"))
        except ValueError:
            turret_x = 0 
    #If we time out, and the return isn't propogating, return none, and
    #we'll give up on that frame and stay put for the time being       
    else:
        turret_x = None

    #Get Y
    self.writeThread.write("\n")
    self.writeThread.write("m 1 \n")
    timeout = 5000000
    while not FEEDBACK and timeout > 0:
        timeout -= 1
        continue 
    if FEEDBACK:       
        try:
            line = FEEDBACK.pop()
            print "Line reads: %s" % line
            _, _, turret_y = line.split(" ")
            turret_y = int(turret_y.rstrip("\n"))
        except ValueError:
            turret_y = 0    
    #If we time out, and the return isn't propogating, return none, and
    #we'll give up on that frame and stay put for the time being       
    else:
        turret_y = None

    return turret_x, turret_y
 
def centering_state(self, curr_frm_cir, img):
    '''curr_frm_cir - The circles found within the segemnted image. Will be
            in the form of a tuple for each circle- (x, y, radius)
        img- The original unmodified input image.
    '''

    global LOCK_TIMER    
    global ALPHA_CIRCLE

    matched_pairs = find_shortest_distances(curr_frm_cir)
    PREV_COORDS = curr_frm_cir[:]
    
    future_locs = anticipate_the_future(matched_pairs)  
    
    for moving_circles in future_locs:
        #Once we do away with lime lines, can get rid of this and just call
        #determine_alpha_circle with future_locs
        current_x, current_y = moving_circles[0]
        future_x, future_y = moving_circles[1] 

        img.dl().line((current_x, current_y), (future_x, future_y), scv.Color.LIME, 4)
    
    alpha_circle = determine_alpha_circle(future_locs, curr_frm_cir)
    print "Alpha Circle: %s" % alpha_circle
    print "Lock is currently: %s" % LOCK_TIMER
    #give command here to move to alpha
    #Alpha- [(curr_x, curr_y), (fut_x, fut_y), curr_r]
    ALPHA_CIRCLE = alpha_circle[:]    
    
    LOCK_TIMER = LOCK_AMT

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
        #Want to use all my globals in here.
        global display, cam, normalDisplay
        global PREV_COORDS
        global ALPHA_CIRCLE
        global LOCK_TIMER        
        global SEEK_LIST
        global RE_SEEK
        
        x_inc = 0
        y_inc = 0

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

            #If we are currently locked on a target (have found alpha). Want to
            #shoot it, despite having lost it.    
            if LOCK_TIMER:
                #Get the current position, and translate it back into our scale
                curr_x, curr_y = get_turret_xy(self)
                curr_x = (curr_x / 5000 * 512) + 512 
                curr_y = (curr_y / 5000 * 384) + 384
                print "Curr_Pos- %s, %s" % (curr_x, curr_y)
                
                if LOCK_TIMER == LOCK_AMT:
                    #Want to do the increment calculation up front so that it
                    #can just step towards it on the lock steps. When it gets there,
                    #change to follow.
                    fut_alpha_x, fut_alpha_y = ALPHA_CIRCLE[1]        
           
                    x_inc = (fut_alpha_x - curr_x) / 5
                    y_inc = (fut_alpha_y - curr_y) / 5
     
                LOCK_TIMER -= 1

                #Getposition we would want it to move to.
                move_x = curr_x + x_inc
                move_y = curr_y + y_inc     
                print "Our move: %s, %s" % (move_x, move_y)                 
 
                #Translate back.
                move_x = (move_x - 512) * 5000 / 512
                move_y = (move_y - 384) * 5000 / 384
                print "Turret move: %s, %s" % (move_x, move_y)                 
 
                print "Alpha in lock: %s" % ALPHA_CIRCLE
                print "Increments of %s, %s" % (x_inc, y_inc)
                print "Sending to (%s, %s) from C:(%s,%s) . L:%s" % (move_x, move_y, curr_x, curr_y, LOCK_TIMER)
                '''self.writeThread.write("\n")
                self.writeThread.write("m 0 %s\n" % str(curr_x + x_inc))
                self.writeThread.write("\n")
                self.writeThread.write("m 1 %s\n" % str(curr_y + y_inc))
                '''
                self.writeThread.write("\n")
                self.writeThread.write("m 0 %s\n" % move_x)
                self.writeThread.write("\n")
                self.writeThread.write("m 1 %s\n" % move_y)
            
            #Entering state where we have found circles, now want to start tracking.
            elif blobs and circles:
                
                curr_frm_cir = map(lambda b: (b.x, b.y, b.radius()), circles)
               
                for b in circles:
                    b.drawOutline(scv.Color.RED, width=4, layer= img.dl())
                    b.drawOutline(scv.Color.RED, width=4, layer= segmented.dl())
                    
                    centering_state(self, curr_frm_cir, img) 
                    
                    #Set the previous coordinates to the current, since we're moving
                    #to the next frame.
                    PREV_COORDS = curr_frm_cir[:]    
                #Want to reset so next time we have to seek we can start again.
                RE_SEEK = True            
            
            #There are no circles found, and lock timer has hit 0, instead want to 
            #enter a seek state.
            else:
                rand_idx = randrange(4)
                trg_x, trg_y = SEEK_LIST[rand_idx] 
                
                #Get current position and translate to us
                turret_x, turret_y = get_turret_xy(self)
                turret_x = (turret_x / 5000 * 512) + 512 
                turret_y = (turret_y / 5000 * 384) + 384
                 
                #If there was a hang on either one, will return None, and want
                #to skip this frame
                if turret_x is None or turret_y is None:
                    continue
                
                ALPHA_CIRCLE = [(turret_x, turret_y), (trg_x, trg_y), None]
                print "Setting seek alpha %s" % ALPHA_CIRCLE
                LOCK_TIMER = LOCK_AMT
                continue
                '''P
                if RE_SEEK:
                    #Alpha- [(curr_x, curr_y), (fut_x, fut_y), curr_r]
                    ALPHA_CIRCLE = [(turret_x, turret_y), (trg_x, trg_y), None]
                    print "Setting seek alpha %s" % ALPHA_CIRCLE
                    LOCK_TIMER = LOCK_AMT
                    RE_SEEK = False
                else:
                    #seek_state(self, turret_x, turret_y)       
                    alpha_x, alpha_y = ALPHA_CIRCLE[1]    
                    curr_x, curr_y = ALPHA_CIRCLE[0]

                    x_inc = (alpha_x - curr_x) / 30  
                    y_inc = (alpha_y - curr_y) / 30  
                    print "T:%s, T_I:%s" % (type(turret_x), type(x_inc))
                    print "Move from %s, %s by %s, and %s" % (turret_x, turret_y, x_inc, y_inc) 
                    print "Seeking to (%s, %s) from C:(%s,%s) to A:(%s,%s). L:%s" % (curr_x+ x_inc, curr_y +y_inc, curr_x, curr_y, alpha_x, alpha_y, LOCK_TIMER)
                    self.writeThread.write("\n")
                    self.writeThread.write("m 0 %s\n" % str(turret_x + x_inc)) 
                    self.writeThread.write("\n")
                    self.writeThread.write("m 1 %s\n" % str(turret_y + y_inc)) 
                '''
            if normalDisplay:
                img.show()
            else:
                segmented.show()

controller = turretController(CONTROLFILE)
controller.main()
