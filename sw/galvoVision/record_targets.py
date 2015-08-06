import argparse

import cv2
import numpy as np


def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("v_input", type=int,
                        help="Which camera should be used in case of multiple.")
    args = parser.parse_args()

    return args

def main():

    args = parse_args()

    cap = cv2.VideoCapture(args.v_input)
    cap.set(3, 1920)
    cap.set(4, 1080)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print "Reading with W: {}, H: {}".format(w, h)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi', fourcc, 20.0, (w, h))

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # frame = cv2.flip(frame,0)
            # write the flipped frame
            out.write(frame)

            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break

    # Release everything if job is finished
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()