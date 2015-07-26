import argparse
from math import sqrt
import threading
import time
from sys import maxint


import cv2
import numpy as np


class cameraReadThread(threading.Thread):
    def __init__(self, cam):
        super(cameraReadThread, self).__init__()
        self.cap = cv2.VideoCapture(cam)
        # self.cap.set(3, 1920)
        # self.cap.set(4, 1080)
        w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print("Resolution: (" + str(int(w)) + "," + str(int(h)) + ")")

        self.running = 1
        self.frameReady = False

    def run(self):
        while self.running:
            _, self.frame = self.cap.read()
            self.frameReady = True

    def getFrame(self):
        while(self.frameReady == False):
            time.sleep(0.001)

        self.frameReady = False
        return self.frame

def parse_args():
   
    parser = argparse.ArgumentParser()
    # parser.add_argument("background", help="File which acts as the base unchanged image.")
    # parser.add_argument("changed", help="File which acts as the changed image.")
    parser.add_argument("v_input", type=int, help="Which camera should be used in case of multiple.")
    parser.add_argument('--template', help="Optional image to match on.")
    args = parser.parse_args()

    return args

def main():

    args = parse_args()

    cam = args.v_input
    cameraThread = cameraReadThread(cam)
    cameraThread.daemon = True

    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.namedWindow('masked', cv2.WINDOW_NORMAL)
    cv2.namedWindow('contours', cv2.WINDOW_NORMAL)

    fgbg = cv2.createBackgroundSubtractorMOG2()
    #fgbg = cv2.createBackgroundSubtractorKNN()

    cameraThread.start()
    LOCKED = False
    prev_contour_set = None

    print args

    while (True):

        future_pairs = []
        # if LOCKED:
        #     frame = mask_original_frame(cameraThread.getFrame(), (l_bound, r_bound, u_bound, b_bound))
        # else:
        #     frame = cameraThread.getFrame()
        frame = cameraThread.getFrame()
        movement_mask = fgbg.apply(frame)

        cv2.imshow('image', frame)

        contours = use_feature_contours(movement_mask)

        n_contours, LOCKED = get_n_contours(contours, 1)
        if LOCKED and n_contours:
            if prev_contour_set:
                matched_coords = find_shortest_distances(prev_contour_set, n_contours)
                future_pairs = anticipate_the_future(matched_coords)

            prev_contour_set = n_contours

            # #Get extents of current contour set
            # l_bound, r_bound, u_bound, b_bound = get_mask_coords(n_contours)
            # print (l_bound, r_bound, u_bound, b_bound)
        # if n_contours:
        #     live_trgs, dead_trgs = racial_profile(frame, n_contours)

        draw(frame, n_contours, future_pairs)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def get_mask_coords(n_contours):

    print "Running get coords on contour of %s size" % cv2.contourArea(n_contours[0])

    leftmost = min([tuple(cnt[cnt[:,:,0].argmin()][0])[0] for cnt in n_contours])
    rightmost = max([tuple(cnt[cnt[:,:,0].argmax()][0])[0] for cnt in n_contours])
    topmost = min([tuple(cnt[cnt[:,:,1].argmin()][0])[1] for cnt in n_contours])
    bottommost = max([tuple(cnt[cnt[:,:,1].argmax()][0])[1] for cnt in n_contours])

    return leftmost, rightmost, topmost, bottommost

def use_feature_contours(mask):

    cp = mask.copy()
    cv2.imshow('masked', cp)
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


def draw(img_out, contours, future_pairs):
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

    cv2.imshow('contours', vis)


def get_n_contours(all_contours, n):
    """
    Get the n largest contours in the set.
    """
    areas = np.array([cv2.contourArea(c) for c in all_contours])

    max_indices = np.argsort(-areas)[:n]
    max_contours = [all_contours[idx] for idx in max_indices]

    locked = all([cv2.contourArea(x) > 100 for x in max_contours])

    return max_contours, locked


def mask_original_frame(frame, coords):
    mask = np.zeros(frame.shape[:2], np.uint8)

    # Coords are L, R, T, B
    cv2.rectangle(mask, (coords[0], coords[2]), (coords[1], coords[3]), 255, -1)
    return cv2.bitwise_and(frame, frame, mask=mask)


def draw_bounding_rect(out_img, contours, filled=False):

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


