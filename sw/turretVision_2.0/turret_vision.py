'''Webcams learn to detect blue circles, take two.'''

import datetime
import os
import SimpleCV as scv
import argparse as arg
import numpy as np
import sys

from math import sqrt

display = scv.Display(resolution=(960,720))
cam = scv.Camera(1, {"height": 768, "width": 1024})
normalDisplay = True

prev_coords = [(0,0)]

def find_shortest_distances(curr):
    '''Naively assume that for a single coord, shortest distance
    will be a 1-to-1 for all in both curr set and prev set.'''
    master_set = []
    
    for x,y in curr:
        print "X:%s,Y:%s, prev:%s" % (x, y, prev_coords)  
        best_dist = sys.maxint
        best_pair = None    

        for p_x, p_y in prev_coords:
            print "Are getting into 0,0 look."
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

        new_x = first_x + (sec_x-first_x)
        new_y = first_y + (sec_y-first_y)

        future_locs.append([(sec_x,sec_y), (new_x, new_y)])
   
    return future_locs 

print "Prev coords: %s" % prev_coords        
while display.isNotDone():
    
    img = cam.getImage().flipHorizontal()

    if display.mouseRight:
        break
    if display.mouseLeft:
        normalDisplay = not(normalDisplay)

    segmented = img.colorDistance(scv.Color.WHITE).dilate(2).binarize(25)
    #segmented = np.where(segmented < 200, 0, segmented)
    blobs = segmented.findBlobs(minsize=200, maxsize=7000)

    if blobs:
        
        circles = filter(lambda b: b.isCircle(0.4), blobs)
        curr_coords = map(lambda b: (b.x, b.y), circles)
        for b in circles:
            b.drawOutline(scv.Color.RED, width=4, layer= img.dl())
            b.drawOutline(scv.Color.RED, width=4, layer= segmented.dl())
        
        matched_pairs = find_shortest_distances(curr_coords)
        prev_coords = curr_coords[:]
        
        if circles:
            future_locs = anticipate_the_future(matched_pairs)  
     
            for coords in future_locs:
                current = coords[0]
                future_x, future_y = coords[1] 
                
                future_x = future_x * 2 if future_x * 2 < 960 else 959
                future_y = future_y * 2 if future_y* 2 < 720 else 719

                img.dl().line(current, (future_x, future_y), scv.Color.LIME, 4)

    if normalDisplay:
        img.show()
    else:
        segmented.show()
    

 
