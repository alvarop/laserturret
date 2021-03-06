import cv2
import numpy as np

def nothing(x):
    pass

normalDisplay = True

#Setting up the parts themselves
cv2.namedWindow('image')
cv2.createTrackbar('Contrast', 'image', 1,3, nothing)
cv2.createTrackbar('Brightness', 'image', 50, 100, nothing) 

# create switch for ON/OFF functionality
switch = '0 : NORM \n1 : SEG'
cv2.createTrackbar(switch, 'image',0,1,nothing)

def main():

    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Capture could not be opened successfully.") 

    while True:
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        _, img = cap.read()

        alpha = cv2.getTrackbarPos('Contrast', 'image')
        #Sliders can't be lower than 0, so starting at 50, then subtracting
        beta = cv2.getTrackbarPos('Brightness', 'image') - 50
        print beta

        toggle = cv2.getTrackbarPos(switch, 'image')
        segmented = False if toggle == 0 else True
        
        #trans_img = cv2.add(mul_img, b_array)
        trans_img = (alpha * img)       
        #trans_img = np.where(trans_img + beta >= 0, trans_img + beta, 0)
        

        if segmented:
            gray = cv2.cvtColor(trans_img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            cv2.imshow('image', binary)
        else:
            cv2.imshow('image', trans_img)
main()   
