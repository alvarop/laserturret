#include <iostream>
#include <fstream>
#include <opencv2/opencv.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <stdlib.h>

using namespace std;
using namespace cv;

ofstream controlfile;

static float xCenter;
static float yCenter;

// Image dimensions
#define WIDTH (640)
#define HEIGHT (480)

// Circle detection sizes
// TODO - make command-line arguments
#define MIN_RADIUS (5)
#define MAX_RADIUS (40)

void moveX(int32_t deviation) {
	float fPos;
	int32_t velocity = 0;
	
	fPos = (float)deviation/WIDTH;
	
	// Clipping
	if(fPos < -0.5) {
		fPos = -0.5;
	} else if (fPos > 0.5) {
		fPos = 0.5;
	}
	
	velocity -= fPos * 200;
	
	controlfile << "qik 0 mov " << velocity << "\n" << endl;
	cout << "qik 0 mov " << velocity << "\n" << endl;
}

void moveY(int32_t deviation) {
	float fPos;
	int32_t velocity = 0;
	
	fPos = (float)deviation/HEIGHT;

	if(fPos < -0.5) {
		fPos = -0.5;
	} else if (fPos > 0.5) {
		fPos = 0.5;
	}
		
	velocity -= fPos * 200;

	controlfile << "qik 1 mov " << velocity << "\n" << endl;
	cout << "qik 1 mov " << velocity << "\n" << endl;
}

uint32_t distanceFromCenter(uint32_t x, uint32_t y) {
	// Ignore sqrt for now, since all we care is about relative distance
	int32_t xDis = xCenter - x;
	int32_t yDis = yCenter - y;
	return xDis * xDis + yDis * yDis;
}

int main(int argc, char ** argv) { 
	
	if(argc < 3) {
		cout << "Usage: <serial device (/dev/ttyACM0)> <camera id (0,1,2...)> [xOffset yOffset]" << endl;
		return -1;
	}

	xCenter = WIDTH/2;
	yCenter = HEIGHT/2;

	// Adjust for laser center using command-line arguments
	if(argc > 4) {
		xCenter += strtol(argv[3], NULL, 0);
		yCenter += strtol(argv[4], NULL, 0);
	}

	cout << "xCenter: " << xCenter << " yCenter: " << yCenter << endl; 

	controlfile.open(argv[1], ios::out);
	
	// Make sure the motors are not moving
	controlfile << "qik 0 mov 0\n" << endl;
	controlfile << "qik 1 mov 0\n" << endl;
	
	// Make sure laser is off
	controlfile << "laser 0\n" << endl;

	VideoCapture cap(strtoul(argv[2], NULL, 10));

	if(!cap.isOpened()) {
		cout << "Capture could not be opened successfully" << endl;
		return -1;
	}

	namedWindow("Video");

	while(char(waitKey(1)) != 'q' && cap.isOpened()) {
		uint32_t mainCircle = 0;
		uint32_t mainCircleDistance = UINT32_MAX;

		Mat frame;
		cap >> frame;

		if(frame.empty()) {
			cout << "Video Over" << endl;
			break;
		}

		Mat cimg;
		medianBlur(frame, frame, 5);
		cvtColor(frame, cimg, CV_BGR2GRAY);

		vector<Vec3f> circles;
		HoughCircles(cimg, circles, CV_HOUGH_GRADIENT, 1, 10,
					 100, 30, MIN_RADIUS, MAX_RADIUS // change the last two parameters
									// (min_radius & max_radius) to detect larger circles
					 );

		
		// Figure out which detected circle is closest to the center
		for( size_t i = 0; i < circles.size(); i++ )
		{
			Vec3i c = circles[i];
			if(distanceFromCenter(c[0], c[1]) < mainCircleDistance) {
				mainCircle = i;
				mainCircleDistance = distanceFromCenter(c[0], c[1]);
			}
		}

		if(circles.size()) {
			Vec3i c = circles[mainCircle];
			
			cout << "x:" << c[0] << " y:" << c[1] << " deviation: " << (xCenter - c[0]) << endl;
			
			if((c[0] > (xCenter - c[2])) && (c[0] < (xCenter + c[2]))
				&& (c[1] > (yCenter - c[2])) && (c[1] < (yCenter + c[2]))) {
				controlfile << "laser 1\n" << endl;
				cout << "shoot!" << endl;
			} else {
				controlfile << "laser 0\n" << endl;
				
				// Only move if not centered
				if((c[0] < (xCenter - c[2])) || (c[0] > (xCenter + c[2]))) {
					moveX(xCenter - c[0]);
				} else {
					// Stop moving (only for gearmotors!)
					moveX(0);
				}
				
				// Only move if not centered
				if((c[1] < (yCenter - c[2])) || (c[1] > (yCenter + c[2]))) {
					moveY((yCenter - c[1]));
				} else {
					moveY(0);
				}
			}
			
			// Draw around the circle we're targeting
			circle( cimg, Point(c[0], c[1]), c[2], Scalar(0,0,255), 3, CV_AA);
			circle( cimg, Point(c[0], c[1]), 2, Scalar(0,255,0), 3, CV_AA);
		} else {
			// If there are no circles, stop moving
			// TODO - start searching for others?
			controlfile << "qik 0 mov 0\n" << endl;
			controlfile << "qik 1 mov 0\n" << endl;
			controlfile << "laser 0\n" << endl;
		}
		
		imshow("Video", cimg);
	}

	controlfile << "laser 0\n" << endl;
	
	// Stop motors
	controlfile << "qik 0 mov 0\n" << endl;
	controlfile << "qik 1 mov 0\n" << endl;
	
	// Start coasting
	controlfile << "qik 0 coast\n" << endl;
	controlfile << "qik 1 coast\n" << endl;

	controlfile.close();

	return 0;
}
