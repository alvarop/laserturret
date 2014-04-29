import io
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--serial", type=str, default='/dev/ttyACM0') 
parser.add_argument("-c", "--camera", type=int, default=1) 
parser.add_argument("--xoffset", type=int, default=10) 
parser.add_argument("-c", "--yoffset", type=int, default=-12) 
ARGS = parser.parse_args()

WIDTH = 640
HEIGHT = 480

MAX_RADIUS = 40
MIN_RADIUS = 2

MIN_VELOCITY = 11

CONTROLFILE = io.open(ARGS.s, mode='wt')

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


#--serial /dev/ttyACM0 —camera 1 --xOffset 10 --yOffset -12


