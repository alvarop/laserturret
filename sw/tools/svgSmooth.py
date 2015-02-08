#
# SVG smoothing test
# Load SVG, fit curves, save (and compares!)
# (Doesn't actually smooth yet, just draws straight lines instead)
# Requires svg.path (https://github.com/regebro/svg.path)
#

import sys
from svg.path import parse_path
from xml.dom import minidom

def makeSVG(pathXMLStrings, viewBox):
	xmlStr = '''
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
	xmlns:dc="http://purl.org/dc/elements/1.1/"
	xmlns:cc="http://creativecommons.org/ns#"
	xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
	xmlns:svg="http://www.w3.org/2000/svg"
	xmlns="http://www.w3.org/2000/svg"
	width="''' + str(int(viewBox[2])) + '''mm"
	height="''' + str(int(viewBox[3])) + '''mm"
	viewBox="0 0 ''' + str(int(viewBox[2])) + ''' ''' + str(int(viewBox[3])) + '''">
'''

	xmlStr += '\t<g id="layer1">\n'

	for pathString in pathXMLStrings:
		xmlStr += '\t\t' + pathString + '\n'

	xmlStr += '\t</g>\n</svg>'

	return xmlStr
	
def getPaths(filename):
	doc = minidom.parse(filename)
	path_strings = [path.getAttribute('d') for path in doc.getElementsByTagName('path')]
	
	
	# TODO - also get bounding box for scaling
	viewBoxString = doc.getElementsByTagName('svg')[0].getAttribute('viewBox').split()

	viewBox = [float(viewBoxString[0]), float(viewBoxString[1]), float(viewBoxString[2]), float(viewBoxString[3])]

	doc.unlink()

	return path_strings, viewBox

def path2SVGPath(path, viewBoxSrc):
	pathStr = 'm ' +  str(path[0].start.real) + ',' + str(path[0].start.imag) + ' '
	
	for item in path:
		pathStr += 'L ' + str(item.start.real) + ',' + str(item.start.imag) + ' ' + str(item.end.real) + ',' + str(item.end.imag) + ' '

	return pathStr

def pathStringToXML(pathString, pathName, color):
	xmlStr = '<path id="' + pathName + '" d="'
	xmlStr += pathString
	xmlStr += '" style="fill:none;fill-rule:evenodd;stroke:' + color + ';stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" />'

	return xmlStr

pathStrings, viewBoxSrc = getPaths(sys.argv[1])
pathId = 0

pathXMLStrings = []

for pathString in pathStrings:
	pathXMLStrings.append(pathStringToXML(pathString, "oldPath" + str(pathId), "#FF0000"))
	pathXMLStrings.append(pathStringToXML(path2SVGPath(parse_path(pathString), viewBoxSrc), "newPath" + str(pathId), "#000000"))
	pathId += 1;

print makeSVG(pathXMLStrings, viewBoxSrc)
