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
    cv2.namedWindow('webcam', cv2.WINDOW_NORMAL)

    cap = cv2.VideoCapture(args.v_input)
    fgbg = cv2.BackgroundSubtractorMOG()
    # fgbg2 = cv2.BackgroundSubtractorMOG2()
    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))

    print args

    while (True):

        _, frame = cap.read()

        mog_sub = fgbg.apply(frame)
        # ret,thresh = cv2.threshold(mog_sub,127,255,0)

        # fgmask = cv2.dilate(mog_sub, kernel)
        # vis = np.concatenate((mog_sub, thresh), axis=0)
        cv2.imshow('image', mog_sub)
        # cv2.imshow('image2', thresh)

        if args.template:
            use_match_detection(frame, args.template)
        else:
            use_feature_contours(mog_sub, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def use_match_detection(frame, template):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    template = cv2.imread(template, 0)
    w, h = template.shape[::-1]

    res = cv2.matchTemplate(gray_frame,template,cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)

    cp_frame = frame.copy()

    for pt in zip(*loc[::-1]):
        cv2.rectangle(cp_frame, pt, (pt[0] + w, pt[1] + h), (0,0,255), 2)

    cv2.imshow('webcam', cp_frame)

def use_feature_contours(mask, frame):
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cv2.drawContours(frame, contours, 0, (0,255,0), 3)
        cv2.imshow('webcam', frame)

if __name__ == '__main__':
        main()
