import SimpleCV as scv

from SimpleCV.Shell import plot

def main():
    
    display = scv.Display(resolution=(800,600))
    
    no_circle_uri = './two_circle_single_detect.png'

    #no_circle_uri = './single_circle_no_detect.png'
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

    pared_image = no_circle.hueDistance(165)

    blobs = pared_image.findBlobs(minsize=200)
    #.2 is the tolerance for matching a perfect circle. Higher the number, the more things
    #the filter will allow.
    blobs = blobs.filter([b.isCircle(0.2) for b in blobs])

    for b in blobs:
        #print "lookin at blob"
        #if b.isCircle(tolerance=.1):
        #    print "found circle!"    
        no_circle_out.drawCircle((b.x, b.y), b.radius(), scv.Color.RED, 5)
        #    print ("Circle X: %s, Y: %s, Radius: %s" % (b.x, b.y, b.radius()))

    no_circle_out.save('./testing_prev_undetected_left.png') 

    normal_disp = True

    while display.isNotDone():

        if display.mouseRight:
            break

        if display.mouseLeft:
            normal_disp = not(normal_disp)

        if normal_disp:
            no_circle_out.show()
        else:
            pared_image.show()
main()

