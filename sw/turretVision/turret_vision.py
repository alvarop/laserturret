import io

WIDTH = 640
HEIGHT = 480

MAX_RADIUS = 40
MIN_RADIUS = 2

MIN_VELOCITY = 11

CONTROLFILE = io.open('./testfile.text', mode='wt')

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

