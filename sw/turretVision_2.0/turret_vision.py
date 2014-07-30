'''Webcams learn to detect blue circles, take two.'''

import SimpleCV
import datetime
import os

display = SimpleCV.Display()
cam = SimpleCV.Camera(1, {"height": 1000, "width": 1000})
normalDisplay = True

while display.isNotDone():
    
    if display.mouseRight:
        break
    '''
    img = cam.getImage()
    circles = img.findCircle()

    try:
        for c in circles:
            img.draw(color=SimpleCV.Color.RED, width=5)
    except TypeError:
        continue 

    img.show()
    '''
    if display.mouseLeft:
		normalDisplay = not(normalDisplay)
		print "Display Mode:", "Normal" if normalDisplay else "Segmented" 
        
    img = cam.getImage().flipHorizontal()
    dist = img.colorDistance(SimpleCV.Color.BLACK).dilate(2)
    segmented = dist.stretch(200,255)
    blobs = segmented.findBlobs()
    if blobs:
        circles = blobs.filter([b.isCircle(0.2) for b in blobs])
        if circles:
            img.drawCircle((circles[-1].x, circles[-1].y), circles[-1].radius(),SimpleCV.Color.BLUE,3)
    if normalDisplay:
        img.show()
    else:
        #segmented.show()
        dt = str(datetime.datetime.now())
        dt = dt.replace(' ', '_')
        img.save('./circle_capture_' + dt + '.png')
        normalDisplay = not(normalDisplay)
