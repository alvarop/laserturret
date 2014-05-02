import io
import argparse
import cv2
import numpy as np
import sys

parser = argparse.ArgumentParser()
parser.add_argument("serial", type=str, default='/dev/ttyACM0') 
parser.add_argument("-c", "--camera", type=int, default=1) 
parser.add_argument("--xoffset", type=int, default=10) 
parser.add_argument("--yoffset", type=int, default=-12) 
ARGS = parser.parse_args()

WIDTH = 640
HEIGHT = 480

MIN_VELOCITY = 11

CONTROLFILE = io.open(ARGS.serial, mode='wt')

def move_x(deviation):

    f_pos = deviation / WIDTH

    f_pos = -0.5 if f_pos < -0.5 else 0.5
    velocity = -f_pos * 200

    if velocity < 0 and velocity > -MIN_VELOCITY:
        velocity = -MIN_VELOCITY
    elif velocity > 0 and velocity < MIN_VELOCITY:
        velocity  = MIN_VELOCITY

    CONTROLFILE.write("qik 0 mov %s \n" % velocity)
    print("qik 0 mov %s \n" % velocity)

def move_y(deviation):

    f_pos = deviation / HEIGHT

    f_pos = -0.5 if f_pos < -0.5 else 0.5
    velocity = -f_pos * 200

    if velocity < 0 and velocity > -MIN_VELOCITY:
        velocity = -MIN_VELOCITY
    elif velocity > 0 and velocity < MIN_VELOCITY:
        velocity  = MIN_VELOCITY

    CONTROLFILE.write("qik 1 mov %s \n" % velocity)
    print("qik 1 mov %s \n" % velocity)

def main():

    x_center = WIDTH/2
    y_center = HEIGHT/2

    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Capture could not be opened successfully.")

    while (True):

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        _, frame = cap.read()

        time_on_target = 0
        time_before_relock = 0

        #Blur image to reduce noice
        cv2.medianBlur(frame, 5, frame)

        #Convert to grayscale
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        #Find circles
        max_radius = 40
        min_radius = 2
        circles = cv2.HoughCircles(frame,cv2.cv.CV_HOUGH_GRADIENT, 1, 10,
                        param1=100, param2=30, minRadius=min_radius,maxRadius=max_radius)

        cv2.imshow('frame', frame)

        #If light in frame flickers, time to remain on the target
        if time_on_target > 0:
            time_on_target -= 1

        track_circle_dist = None
        #If we are currently tracking a target, draw it.
        if time_before_relock > 0 and track_circle_dist < 1000:
            cv2.circle(frame, (x_center, y_center), track_circle_dist, (128, 128, 128))
            
            #Decrement to tell us when we should give up and find a new target.
            time_before_relock -= 1
        else:
            #Reset to large circle and begin search again.
            track_circle_dist = 1000

        closest_circle = None
        close_circle_dist = None
        #For some reason, circles is nested.
        for c in circles[0]:
            
            x, y, radius = c.tolist()

            dist_from_center = distance_from_center(x-x_center,y-y_center) 
            if dist_from_center < close_circle_dist:
                close_circle_dist = dist_from_center
                closest_circle = c

        track_circle_dist = 0
        #Conditionals for moving tracking circle
        if time_on_target != 0 and track_circle_dist < close_circle_dist:
            circles = None

        elif time_on_target != 0 and track_circle_dist > close_circle_dist:
            track_circle_dist = close_circle_dist * 1.4
            time_on_target = 20
        elif time_on_target == 0:
            track_circle_dist = close_circle_dist * 1.4
            time_on_target = 10
           
def distance_from_center(x_dist, y_dist):
    '''Euclidean distance from center of a frame.'''
    return math.sqrt(x_dist**2 + y_dist**2)

main()
