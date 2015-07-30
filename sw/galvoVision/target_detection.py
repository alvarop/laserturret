import argparse
from math import sqrt
import threading
import time
from sys import maxint

import cv2
import numpy as np

from galvoVision.calibrate import cameraReadThread, serialReadThread

INIT_STATE = True
LOCKED_STATE = False
SHOOT_STATE = False
C_EXTENTS = None
FC_BOUNDS = None

def parse_args():
   
    parser = argparse.ArgumentParser()
    parser.add_argument("v_input", type=int,
                        help="Which camera should be used in case of multiple.")
    parser.add_argument('--template', help="Optional image to match on.")
    args = parser.parse_args()

    return args

def main():
    global INIT_STATE, LOCKED_STATE, SHOOT_STATE, C_EXTENTS, FC_BOUNDS

    args = parse_args()

    cam = args.v_input
    cameraThread = cameraReadThread(cam)
    cameraThread.daemon = True
    cameraThread.start()

    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.namedWindow('masked', cv2.WINDOW_NORMAL)
    cv2.namedWindow('contours', cv2.WINDOW_NORMAL)

    fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=False)

    prev_contour_set = None


    while (True):

        frame = cameraThread.getFrame()
        movement_mask = fgbg.apply(frame)

        if INIT_STATE:
            '''In init state, no suitable contours detected.
            ACTION: Search FULL image for contours.
            MOVES TO: LOCKED STATE
            CONDITION: Have n contours of suitable size.
            '''
            contours = all_feature_contours(movement_mask)
            n_contours = get_n_contours(contours, 1)

            print "Leaving if init."

        elif LOCKED_STATE:
            '''Locked to trgs, n suitable contours detected.
            ACTION:
                - Clip incoming frame to a std size.
                - Continue to detect contours on smaller frame.
                >> Follow targets
                - Get mean color of each known contour.
                >> Determine future location
                >> Determine alpha trg.
                >> Determine target order.
            MOVES TO: SHOOTING STATE
            CONDITION: Have alpha target, it's blue, and know what number it is.
            '''
            print "Entering if locked."
            # Slice needs to be y, x, starts at upper left corner.
            # frame = frame[FC_BOUNDS[0]:FC_BOUNDS[1],
            #         FC_BOUNDS[2]:FC_BOUNDS[3], ::]

            contours = all_feature_contours(
                movement_mask[FC_BOUNDS[2]:FC_BOUNDS[3],
                            FC_BOUNDS[0]:FC_BOUNDS[1]]
            )
            n_contours = get_n_contours(contours, 1)

            # Make sure we continue to follow contour extents.
            # Possible that we just shifted to init in here, so need to check
            # before we correct according to new contours.
            if n_contours:
                correct_for_contour_movement(n_contours)
            # if prev_contour_set:
            #     matched_coords = find_shortest_distances(prev_contour_set, n_contours)
            #     future_pairs = anticipate_the_future(matched_coords)
            #
            # prev_contour_set = n_contours
            # live_trgs, dead_trgs = racial_profile(frame, n_contours)
            # draw(frame, n_contours, future_pairs)

            draw(frame, n_contours)

        elif SHOOT_STATE:
            pass

        else:
            print "SOMETHING HAS GONE TERRIBLY WRONG."

        print "Made it to the end."
        cv2.imshow('image', frame)
        cv2.imshow('masked', movement_mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def correct_for_contour_movement(contours):
    global FC_BOUNDS, C_EXTENTS

    update_contour_extents(contours)

    print "Correcting, because C_Extents %s, but FC_BOUNDS %s" % (C_EXTENTS, FC_BOUNDS)
    
    if C_EXTENTS[0] < FC_BOUNDS[0]:
        FC_BOUNDS[0] = max(FC_BOUNDS[0] - 50, 0)
        FC_BOUNDS[1] -= 50
    # Right check
    elif C_EXTENTS[1] > FC_BOUNDS[0]:
        FC_BOUNDS[1] = min(FC_BOUNDS[1] + 50, 1919)
        FC_BOUNDS[0] += 50
    # Top check
    elif C_EXTENTS[2] < FC_BOUNDS[2]:
        FC_BOUNDS[2] = max(FC_BOUNDS[2] - 50, 0)
        FC_BOUNDS[3] -= 50
    elif C_EXTENTS[3] > FC_BOUNDS[3]:
        FC_BOUNDS[3] = min(FC_BOUNDS[0] + 50, 1079)
        FC_BOUNDS[2] += 50


def update_contour_extents(n_contours):
    global C_EXTENTS

    leftmost = \
        min([tuple(cnt[cnt[:,:,0].argmin()][0])[0] for cnt in n_contours])
    rightmost = \
        max([tuple(cnt[cnt[:,:,0].argmax()][0])[0] for cnt in n_contours])
    topmost = \
        min([tuple(cnt[cnt[:,:,1].argmin()][0])[1] for cnt in n_contours])
    bottommost = \
        max([tuple(cnt[cnt[:,:,1].argmax()][0])[1] for cnt in n_contours])

    print "C_Extents are (%s, %s, %s, %s)" % (leftmost, rightmost, topmost, bottommost)
    C_EXTENTS = [leftmost, rightmost, topmost, bottommost]


def shift_to_init():
    global INIT_STATE, LOCKED_STATE
    """
    Lost full set of targets. Go back to init state.
    """
    print "Shifting to INIT state."
    INIT_STATE = True
    LOCKED_STATE = False


def shift_to_locked(contours):
    global INIT_STATE, LOCKED_STATE, C_EXTENTS, FC_BOUNDS
    """
    Input: Set of contours which are of appropriate size to be targets.
    Note: Move to locked state initializes the frame clip
    extents to be the contour extents, stretched by 500 and 250.
    """
    INIT_STATE = False
    LOCKED_STATE = True

    update_contour_extents(contours)
    # Left, Right, Up, Down
    FC_BOUNDS = [C_EXTENTS[0], min(C_EXTENTS[0] + 500, 1919),
                 C_EXTENTS[2], min(C_EXTENTS[2] + 250, 1079)]
    print "Moved to LOCKED with window bounds: %s" % FC_BOUNDS

def all_feature_contours(mask):
    global FC_BOUNDS

    cp = mask.copy()
    _, contours, hierarchy = \
        cv2.findContours(cp, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = [cv2.approxPolyDP(cnt, 3, True) for cnt in contours]

    return contours

def racial_profile(source_img, contours):
    live, dead = [], []

    for h, cnt in enumerate(contours):
        mask = np.zeros(source_img.shape[:2], np.uint8)
        cv2.drawContours(mask, [cnt], 0, 255, -1)

        mean = cv2.mean(source_img, mask=mask)

        if mean[0] > 110 and mean[1] > 110:
            print "Trg %s is dead" % h
            dead.append(cnt)
        else:
            print "Trg %s is live" % h
            live.append(cnt)

    return live, dead


def draw(img_out, contours, future_pairs=None):
    global FC_BOUNDS
    """
    DRAW THE THING. And any additional things you want.
    """
    h, w = img_out.shape[:2]
    vis = np.zeros((h, w, 3), np.uint8)
    cv2.drawContours(vis, contours, -1, (128,255,255), 3, cv2.LINE_AA)

    draw_bounding_rect(vis, contours)
    if future_pairs:
        draw_the_future(vis, future_pairs)
    # draw_bounding_circle(vis, contours)

    # Show current search area.
    cv2.rectangle(vis,
                  (FC_BOUNDS[0], FC_BOUNDS[2]),
                  (FC_BOUNDS[1], FC_BOUNDS[3]),
                  (255, 0, 255), 3)

    cv2.imshow('contours', vis)


def get_n_contours(all_contours, n):
    global LOCKED_STATE
    """
    Get the n largest contours in the set.
    """
    areas = np.array([cv2.contourArea(c) for c in all_contours])

    max_indices = np.argsort(-areas)[:n]
    max_contours = [all_contours[idx] for idx in max_indices]
    # print "Area of MAX: %s" % [cv2.contourArea(x) for x in max_contours]

    print "Looking at contours %s" % [cv2.contourArea(x) for x in max_contours]
    locked = all([8000 > cv2.contourArea(x) > 200 for x in max_contours])

    # all([empty]) is truthy, so need to additionally check if contours
    if locked and max_contours and not LOCKED_STATE:
        print "Shift to lock."
        shift_to_locked(max_contours)
    elif LOCKED_STATE and (not max_contours or not locked):
        "Shift to init."
        shift_to_init()

    return max_contours


def mask_original_frame(frame, coords):
    mask = np.zeros(frame.shape[:2], np.uint8)

    # Coords are L, R, T, B
    cv2.rectangle(mask, (coords[0], coords[2]), (coords[1], coords[3]), 255, -1)
    return cv2.bitwise_and(frame, frame, mask=mask)


def draw_bounding_rect(out_img, contours, filled=2):
    # Filled is 2 by default. If filling is desired, change to -1.

    for c in contours:
        # Now draw bounding box
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(out_img,(x,y),(x+w,y+h),(0,255,0), 2)


def draw_bounding_circle(out_img, contours):

    for c in contours:
        # Or a bounding circle
        (x, y), radius = cv2.minEnclosingCircle(c)
        center = (int(x), int(y))
        radius = int(radius)
        cv2.circle(out_img, center, radius, (0, 0, 255), 3)


def draw_the_future(out_img, future_pairs):

    print "I want to draw %s " % future_pairs
    for pair in future_pairs:
        cv2.line(out_img, pair[0], pair[1], (0, 0, 255), 3)


def find_shortest_distances(curr_cnts, prev_cnts):
    '''Naively assume that for a single coord, shortest distance
    will be a 1-to-1 for all in both curr set and prev set.'''
    master_set = []

    def center(cnt):
        M = cv2.moments(cnt)
        centroid_x = int(M['m10']/M['m00'])
        centroid_y = int(M['m01']/M['m00'])
        return centroid_x, centroid_y

    curr = [center(contour) for contour in curr_cnts]
    prev_coords = [center(contour) for contour in prev_cnts]

    for x,y in curr:
        print "X:%s,Y:%s, prev:%s" % (x, y, prev_coords)
        best_dist = maxint
        best_pair = None

        for p_x, p_y in prev_coords:
            print "P_x: %s, p_y: %s" % (p_x, p_y)
            dist = sqrt((x-p_x)**2 + (y-p_y)**2)
            print "Dist: %s" % dist
            if dist < best_dist:
                best_dist = dist
                best_pair = p_x, p_y
        #Associate current x,y to optimal distance pair
        master_set.append([best_pair, (x,y)])

    return master_set


def anticipate_the_future(matched_pairs):

    print "Matched: %s" % matched_pairs
    future_locs = []

    for coord_set in matched_pairs:

        first_x, first_y = coord_set[0]
        sec_x, sec_y = coord_set[1]

        new_x = first_x + 2*(sec_x-first_x)
        new_y = first_y + 2*(sec_y-first_y)

        future_locs.append([(sec_x,sec_y), (new_x, new_y)])

    print "Future %s " % future_locs
    return future_locs

if __name__ == '__main__':
        main()


