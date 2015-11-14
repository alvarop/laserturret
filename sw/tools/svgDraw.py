#
# Convert SVG to series of c arrays
# Requires svg.path (https://github.com/regebro/svg.path)
#

import sys
from svg.path import parse_path
from operator import itemgetter
from PIL import Image, ImageDraw
from svg.path import parse_path
from xml.dom import minidom

TOTAL_POINTS = 1000
MAX_LEN = 10
MAX_DEV = 4096

def get_paths_strings(filename):
	doc = minidom.parse(filename)
	path_strings = [path.getAttribute('d') for path in doc.getElementsByTagName('path')]
	doc.unlink()

	return path_strings

def get_points_from_path(path_str):
	points = []
	path = parse_path(path_str)

	for x in range(1,(TOTAL_POINTS + 1)):
		point = path.point(x/float(TOTAL_POINTS))
		points.append([point.real, point.imag])

	return points

def draw_path(points, draw):
	for x in range(1,len(points)):
		draw.line([(points[x-1][0]*1024, points[x-1][1]*1024), (points[x][0]*1024, points[x][1]*1024)], fill=(0,255,0))

def normalize_points(points):
	for x in range(len(points)):
		points[x][0] = (points[x][0] - min_x)/int(max_x - min_x)
		points[x][1] = (points[x][1] - min_y)/int(max_y - min_y)

im = Image.new('RGB', (1024,1024))
draw = ImageDraw.Draw(im)

path_strings = get_paths_strings(sys.argv[1])
points = []

min_x = 1e99
min_y = 1e99
max_x = 0
max_y = 0

for path_str in path_strings:
	new_points = get_points_from_path(path_str)
	points.append(new_points)
	local_min_x = min(new_points, key=itemgetter(0))[0]
	local_min_y = min(new_points, key=itemgetter(1))[1]
	local_max_x = max(new_points, key=itemgetter(0))[0]
	local_max_y = max(new_points, key=itemgetter(1))[1]

	if(local_max_x > max_x):
		max_x = local_max_x

	if(local_max_y > max_y):
		max_y = local_max_y

	if(local_min_x < min_x):
		min_x = local_min_x

	if(local_min_y < min_y):
		min_y = local_min_y

for path_points in points:
	normalize_points(path_points)
	draw_path(path_points, draw)

del draw
im.show()
