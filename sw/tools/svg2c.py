#
# Convert SVG to series of c arrays
# Requires svg.path (https://github.com/regebro/svg.path)
#

import sys
from svg.path import parse_path
from xml.dom import minidom

def getPaths(filename):
	doc = minidom.parse(filename)
	path_strings = [path.getAttribute('d') for path in doc.getElementsByTagName('path')]
	
	
	# TODO - also get bounding box for scaling
	viewBoxString = doc.getElementsByTagName('svg')[0].getAttribute('viewBox').split()

	viewBox = [float(viewBoxString[0]), float(viewBoxString[1]), float(viewBoxString[2]), float(viewBoxString[3])]

	doc.unlink()

	return path_strings, viewBox

def path2c(path, pathName, viewBoxSrc, viewBoxDst):
	srcX0 = viewBoxSrc[0]
	srcY0 = viewBoxSrc[1]

	srcXMax = viewBoxSrc[2] - viewBoxSrc[0]
	srcYMax = viewBoxSrc[3] - viewBoxSrc[1]

	dstX0 = viewBoxDst[0]
	dstY0 = viewBoxDst[1]

	dstXMax = viewBoxDst[2] - viewBoxDst[0]
	dstYMax = viewBoxDst[3] - viewBoxDst[1]

	cStr = "path_t " + pathName + "[] = {"
	
	for item in path:
		# Normalize x,y to be floats from 0-1
		x = (item.start.real - srcX0)/srcXMax
		y = (item.start.imag - srcY0)/srcYMax

		# Convert to dst coords
		x = dstX0 + x * dstXMax
		y = dstY0 + y * dstYMax

		# Since we're dealing with integers this time
		x = int(x)
		y = int(y)

		cStr += '{' + str(x) + ', ' + str(y) + '}, '

	cStr += '};'

	return cStr

pathStrings, viewBoxSrc = getPaths(sys.argv[1])
pathId = 0

print '''
typedef struct {
	uint16_t x;
	uint16_t y;
} path_t;
'''

for pathString in pathStrings:
	print path2c(parse_path(pathString), "path" + str(pathId), viewBoxSrc, [0,0,4096,4096])
	pathId += 1;

