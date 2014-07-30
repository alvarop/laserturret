import SimpleCV as scv

from SimpleCV.Shell import plot

def main():
    
    display = scv.Display()

    no_circle_uri = './single_circle_no_detect.png'
    '''detect_circle_uri = './single_circle_detetcted.png'
    two_circle_one_detect_uri = './two_circle_single_detect.png.'

    no_c_img = scv.Image(no_circle_uri)
    hist = no_c_img.histogram(255)

    plot(hist)
    '''
    no_circle = scv.Image(no_circle_uri)
    no_circle_out = scv.Image(no_circle_uri)

    #Generally, the one around 123 is our blue.
    peaks = no_circle.huePeaks()
    print peaks

    pared_image = no_circle.hueDistance(123)

    blobs = pared_image.findBlobs(minsize=30)

    for b in blobs:
        #print "lookin at blob"
        #if b.isCircle(tolerance=.1):
        #    print "found circle!"    
        no_circle_out.drawRectangle(b.x, b.y, 2, 2, scv.Color.YELLOW)
        #    print ("Circle X: %s, Y: %s, Radius: %s" % (b.x, b.y, b.radius()))

    img = no_circle_out

    while display.isNotDone():
        img.show()

        if display.mouseRight:
            break

        if display.mouseLeft:
            img = pared_image
main()
