import argparse
import threading
import time

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

    print args

    while (True):

        frame = cameraThread.getFrame()
        mask = fgbg.apply(frame)
        # ret,thresh = cv2.threshold(mog_sub,127,255,0)

        # vis = np.concatenate((mog_sub, thresh), axis=0)
        cv2.imshow('image', frame)

        # if args.template:
        #     use_match_detection(frame, args.template)
        # else:
        contours = use_feature_contours(mask)

        n_contours, LOCKED = get_n_contours(contours, 1)
        if LOCKED and n_contours:
            l_bound, r_bound, u_bound, b_bound = get_mask_coords(n_contours)
            print (l_bound, r_bound, u_bound, b_bound)
        # if n_contours:
        #     live_trgs, dead_trgs = racial_profile(frame, n_contours)

        draw(frame, n_contours)

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


def draw(img_out, contours):
    """
    DRAW THE THING. And any additional things you want.
    """
    h, w = img_out.shape[:2]
    vis = np.zeros((h, w, 3), np.uint8)
    cv2.drawContours(vis, contours, -1, (128,255,255), 3, cv2.LINE_AA)

    draw_bounding_rect(vis, contours)
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

    # def center(cnt):
    #     M = cv2.moments(cnt)
    #     centroid_x = int(M['m10']/M['m00'])
    #     centroid_y = int(M['m01']/M['m00'])
    #     return centroid_x, centroid_y
    # try:
    #     print [center(x) for x in max_contours]
    # except ZeroDivisionError:
    #     pass

    return max_contours, locked


def draw_bounding_rect(out_img, contours, filled=False):

    for c in contours:
        # Now draw bounding box
        x, y, w, h = cv2.boundingRect(c)
        thickness = -1 if filled else 2
        cv2.rectangle(out_img,(x,y),(x+w,y+h),(0,255,0), thickness)

def draw_bounding_circle(out_img, contours):

    for c in contours:
        # Or a bounding circle
        (x, y), radius = cv2.minEnclosingCircle(c)
        center = (int(x), int(y))
        radius = int(radius)
        cv2.circle(out_img, center, radius, (0, 0, 255), 3)

#def use_match_detection(frame, template):
#     gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)q
#     template = cv2.imread(template, 0)
#     w, h = template.shape[::-1]
#
#     res = cv2.matchTemplate(gray_frame,template,cv2.TM_CCOEFF_NORMED)
#     threshold = 0.8
#     loc = np.where(res >= threshold)
#
#     cp_frame = frame.copy()
#
#     for pt in zip(*loc[::-1]):
#         cv2.rectangle(cp_frame, pt, (pt[0] + w, pt[1] + h), (0,0,255), 2)
#
#     # cv2.imshow('webcam', cp_frame)

if __name__ == '__main__':
        main()


