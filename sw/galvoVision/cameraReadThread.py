# 
# This thread constantly reads out camera frames to minimize the chance of
# getting a stale frame
# 
import threading
import time
import cv2

class cameraReadThread(threading.Thread):
    def __init__(self, cam, width = 1920, height = 1080):
        super(cameraReadThread, self).__init__()
        self.cap = cv2.VideoCapture(cam)
        self.cap.set(3, width)
        self.cap.set(4, height)
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
