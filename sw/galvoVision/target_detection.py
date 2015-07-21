import cv2
import argparse
import numpy as np

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
    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.namedWindow('masked', cv2.WINDOW_NORMAL)
    cv2.namedWindow('contours', cv2.WINDOW_NORMAL)

    cap = cv2.VideoCapture(args.v_input)
    fgbg = cv2.createBackgroundSubtractorMOG2()
    # fgbg = cv2.createBackgroundSubtractorKNN()


    print args

    while (True):

        _, frame = cap.read()

        mog_sub = fgbg.apply(frame)
        # ret,thresh = cv2.threshold(mog_sub,127,255,0)

        # vis = np.concatenate((mog_sub, thresh), axis=0)
        cv2.imshow('image', frame)
        #cv2.imshow('masked', mog_sub)

        # if args.template:
        #     use_match_detection(frame, args.template)
        # else:
        use_feature_contours(mog_sub, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def use_feature_contours(mask, frame):

    cp = mask.copy()
    cv2.imshow('masked', cp)
    _, contours, hierarchy = \
        cv2.findContours(cp, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = [cv2.approxPolyDP(cnt, 3, True) for cnt in contours]

    # Get the largest contour currently found.
    areas = [cv2.contourArea(c) for c in contours]
    max_index = np.argmax(areas)

    h, w = frame.shape[:2]

    # DRAW THE THING
    vis = np.zeros((h, w, 3), np.uint8)
    cv2.drawContours(vis, contours, max_index, (128,255,255), 3, cv2.LINE_AA)

    # Now draw bounding box
    x,y,w,h = cv2.boundingRect(contours[max_index])
    cv2.rectangle(vis,(x,y),(x+w,y+h),(0,255,0),2)

    # Or a bounding circle
    (x,y),radius = cv2.minEnclosingCircle(contours[max_index])
    center = (int(x),int(y))
    radius = int(radius)
    cv2.circle(vis,center,radius,(0,0,255),3)

    cv2.imshow('contours', vis)

#def use_match_detection(frame, template):
#     gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
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


