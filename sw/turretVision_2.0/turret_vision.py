'''Webcams learn to detect blue circles, take two.'''

import io
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

prev_coords = [(0,0, 0)]

#CONTROLFILE = io.open(ARGS.serial, mode='wt')

def find_shortest_distances(curr):
    '''Naively assume that for a single coord, shortest distance
    will be a 1-to-1 for all in both curr set and prev set.'''
    master_set = []
   
    #Don't need the radius for now. 
    for x,y,r in curr:
        best_dist = sys.maxint
        best_pair = None    

        for p_x, p_y, _ in prev_coords:
            dist = sqrt((x-p_x)**2 + (y-p_y)**2)
            
            if dist < best_dist: 
                best_dist = dist
                best_pair = p_x, p_y
        #Associate current x,y to optimal distance pair
        #Pass along radius for later use. This the the r of the current. Assume
        #it will be closer to future size than previous.
        master_set.append([best_pair, (x,y), r])
    
    return master_set

def anticipate_the_future(matched_pairs):

    print "Matched: %s" % matched_pairs
    future_locs = []

    for coord_set in matched_pairs:
    
        first_x, first_y = coord_set[0]
        sec_x, sec_y = coord_set[1]
        r = coord_set[2]

        new_x = first_x + 2 * (sec_x-first_x)
        new_y = first_y + 2 * (sec_y-first_y)

        print("C_X:%s, C_Y:%s, F_X:%s, F_Y:%s" % (sec_x, sec_y, new_x, new_y))          
        future_locs.append([(sec_x,sec_y), (new_x, new_y), r])
   
    return future_locs 

def determine_alpha_circle(moving_circles, frm_cir_coords):
    
    hits_others = True

    current_x, current_y = moving_circles[0]
    future_x, future_y = moving_circles[1] 
    radius = moving_circles[2]               
    
    #Assuming we have circles, want to pick the one which
    #is at the front. Defined as "future direction doesn't
    #run into any others.

    #For the moment, ignoring the radius of the current circle it's
    #comparing against.
    for curr_x, curr_y, _ in frm_cir_coords:
        
        #If we're looking at ourself.
        if (curr_x, curr_y) == (current_x, current_y):
            continue             

        in_x_bounds = future_x-radius < curr_x < future_x + radius
        in_y_bounds = future_y - radius < curr_x < future_y + radius              
        if not in_x_bounds and not in_y_bounds:
            alpha_circle = moving_circles
            hits_others = False
    
    if hits_others:
        alpha_circle = future_locs[0] 

    return alpha_circle

print "Prev coords: %s" % prev_coords        
while display.isNotDone():
    
    img = cam.getImage()
    #img = cam.getImage().flipHorizontal()

    if display.mouseRight:
        break
    if display.mouseLeft:
        normalDisplay = not(normalDisplay)

    segmented = img.colorDistance(scv.Color.WHITE).dilate(2).binarize(25)
    #segmented = np.where(segmented < 200, 0, segmented)
    blobs = segmented.findBlobs(minsize=200, maxsize=7000)

    if blobs:
        
        circles = filter(lambda b: b.isCircle(0.4), blobs)
        curr_frm_cir = map(lambda b: (b.x, b.y, b.radius()), circles)
        for b in circles:
            b.drawOutline(scv.Color.RED, width=4, layer= img.dl())
            b.drawOutline(scv.Color.RED, width=4, layer= segmented.dl())
        
        if circles: 
            matched_pairs = find_shortest_distances(curr_frm_cir)
            prev_coords = curr_frm_cir[:]
            
            future_locs = anticipate_the_future(matched_pairs)  
            
            hits_others = True
            for moving_circles in future_locs:
                #Once we do away with lime lines, can get rid of this and just call
                #determine_alpha_circle with future_locs
                current_x, current_y = moving_circles[0]
                future_x, future_y = moving_circles[1] 
                radius = moving_circles[2]               
 
                img.dl().line((current_x, current_y), (future_x, future_y), scv.Color.LIME, 4)
                alpha_circle = determine_alpha_circle(moving_circles, curr_frm_cir)
                print "Alpha Circle: %s" % alpha_circle


        if normalDisplay:
            img.show()
        else:
            segmented.show()
        

     
