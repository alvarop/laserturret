import SimpleCV as scv
import datetime

from SimpleCV.Shell import plot

def main():
    
    display = scv.Display(resolution=(800,600))
    cam = scv.Camera(0, {"height": 768, "width": 1024})
    normal_disp = True
   
    #vs = scv.VideoStream('/home/kathryn/workspace/saved_video.avi')
    video = scv.VirtualCamera('./train_video.avi', 'video')

    #no_circle_uri = './two_circle_single_detect.png'
    #no_circle_uri = './single_circle_no_detect.png'
    '''detect_circle_uri = './single_circle_detetcted.png'
    two_circle_one_detect_uri = './two_circle_single_detect.png.'

    no_c_img = scv.Image(no_circle_uri)
    hist = no_c_img.histogram(255)

    plot(hist)
    '''
    #no_circle = scv.Image(no_circle_uri)
    #no_circle_out = scv.Image(no_circle_uri)

    while display.isNotDone():
        img = cam.getImage()
        #img.save(vs)
        #img = scv.Image('./reference_img_2.png') 
        img = video.getImage()
        if display.mouseRight:
            break

        if display.mouseLeft:
            #time = datetime.datetime.now().strftime('%M:%S')
            #img.save('./reference_img' + time + '.png')
            normal_disp = not(normal_disp)

        #pared_image = img.colorDistance((215, 215, 255)).binarize(20).dilate(3)
        #pared_image = img.colorDistance((210, 210, 255)).binarize(45)
        #pared_image = img.hueDistance(230)       
        pared_image =img.invert().hueDistance(218, minsaturation=40, minvalue=50).binarize().invert()

        blobs = pared_image.findBlobs(minsize=50, maxsize=7000)
        if blobs:
            circles = blobs.filter([b.isCircle(0.3) for b in blobs])
            c_info = map(lambda b: (b.x, b.y, b.height(), b.width(), b.radius()), circles)
            for c in circles:
                pared_image.dl().circle((c.x, c.y), c.radius(), scv.Color.RED, 4)           
 
            print c_info
 
        #pared_image = img.hueDistance(165)
        #pared_image = img.colorDistance(scv.Color.CYAN)    

        '''
        #Generally, the one around 123 is our blue.
        peaks = no_circle.huePeaks()
        print peaks

        #pared_image = no_circle.hueDistance(165)
        pared_image = no_circle.colorDistance(scv.Color.CYAN)    

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
            print ("Width: %s, Height: %s" % (b.width(), b.height())) 

        no_circle_out.save('./testing_prev_undetected_left.png') 

        normal_disp = True
        '''
        if normal_disp:
            img.show()
        else:
            pared_image.show()
main()

