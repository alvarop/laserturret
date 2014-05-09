#!/usr/bin/env python
# -*- coding: utf-8 -*-
from libavg import avg
from time import gmtime, strftime

def change_text():
    
    #Note: circle node's apparently don't have a text item, so
    #it doesn't do anything to the circle node. I suspect if ms
    #were included in my time string, we would see it change much
    #faster than 1 / s.
    for item in ls:
        item.text = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

player = avg.Player.get()

canvas = player.createMainCanvas(size=(640,480))
rootNode = canvas.getRootNode()

bar = avg.WordsNode(pos=(10,10), font="arial", 
    text="Hello World", parent=rootNode, fontsize=72)
word = avg.WordsNode(text='Hello libavg', pos=(10,30),
    parent=rootNode)

#This will execute the function for every frame of the monitor    
player.setOnFrameHandler(change_text)

#After 1 second, the thing will change, but only once.
player.setTimeout(1000, change_text)

#Every .2 s, will change.
#player.setInterval(200, change_text)

foo = avg.CircleNode(r=10, pos=(200,230),
            fillcolor="0000FF", fillopacity=100,
            parent=rootNode)

foo.color = "FF8000"

ls = [word, foo, bar]

player.play()
