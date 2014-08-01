'''Webcams learn to detect blue circles, take two.'''

import datetime
import os
import SimpleCV as scv
import argparse as arg
import numpy as np

display = scv.Display(resolution=(960,720))
cam = scv.Camera(1, {"height": 768, "width": 1024})
#Figure out what the number param is.
rs = scv.RunningSegmentation(0.5)

normalDisplay = True

flow = np.empty((1024,768)).fill(-1)

while display.isNotDone():
    
    if display.mouseRight:
        break
    if display.mouseLeft:
		normalDisplay = not(normalDisplay)
		print "Display Mode:", "Normal" if normalDisplay else "Segmented" 
    
    img = cam.getImage().flipHorizontal()

    if (rs.isReady()):
        img = rs.getSegmentedImage(False) 
        segmented = (img * 2 - 20).binarize(127).erode(1).invert()
        blobs = segmented.findBlobs(minsize=40, maxsize=7000)

        #If a blob was found, sort based on distance from the coordinate where we
        #last sent the laser. For now, will use the default of the center.
        if blobs:
            
            blobs = blobs.sortDistance()
            b_x = blobs[0].minRectX()
            b_y = blobs[0].minRectY()

            #Here we do laser things to direct it to shoot at the current x and y.
            #Likely will have to involve math.
            img.dl().circle((b_x, b_y), scv.Color.RED, width=3)

    else:
        pass



    if normalDisplay:
        img.save(display)
    else:
        '''
        This code will allow you to save files by left clicking.
        dt = str(datetime.datetime.now())
        dt = dt.replace(' ', '_')
        img.save('./circle_capture_' + dt + '.png')'''
        segmented.save(display)
        normalDisplay = not(normalDisplay)
