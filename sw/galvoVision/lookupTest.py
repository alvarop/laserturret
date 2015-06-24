#!/usr/bin/python
# 
# Read in lookup table and *hopefully* figure out how to do
# a reverse lookup (pixel to laser pos)
# 
import argparse
import cv2
import numpy as np
import math
import timeit
import csv

def nothing(x):
    pass

# im2 = cv2.imread("orig/f2.png")

# 
# Read table into list of lists (i think)
# Format is "laserX, laserY, pixelX, pixelY"
# 
dotTable = []
with open('dotTable.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        dotTable.append([int(row[0]), int(row[1]), int(row[2]), int(row[3])])

# 
# Sort by both pixelX and pixelY for faster lookup (again, I think...)
# 
xSorted = sorted(dotTable, key = lambda x:x[2])
ySorted = sorted(dotTable, key = lambda x:x[3])

for item in xSorted:
    print item

for item in ySorted:
    print item
