#include <iostream>
#include <fstream>
#include <opencv2/opencv.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <stdlib.h>
#include <limits>

using namespace std;
using namespace cv;

ofstream controlfile;

static float xCenter;
static float yCenter;

// Image dimensions
#define WIDTH (640)
#define HEIGHT (480)

static int minVelocityX = 11;
static int minVelocityY = 11;


// Circle detection sizes
// TODO - make command-line arguments
#define MIN_RADIUS (0)
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

	if((velocity < 0) && (velocity > -minVelocityX)) {
		velocity = -minVelocityX;
	} else if((velocity > 0) && (velocity < minVelocityX)) {
		velocity = minVelocityX;
	}
	
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

	if((velocity < 0) && (velocity > -minVelocityY)) {
		velocity = -minVelocityY;
	} else if((velocity > 0) && (velocity < minVelocityY)) {
		velocity = minVelocityY;
	}

	controlfile << "qik 1 mov " << velocity << "\n" << endl;
	cout << "qik 1 mov " << velocity << "\n" << endl;
}

float distanceFromCenter(float x, float y) {
	float xDis = xCenter - x;
	float yDis = yCenter - y;
	return sqrt(xDis * xDis + yDis * yDis);
}

// Checks if point x,y is within a circle centered at cirX,cirY with radius 'radius'
bool isInCircle(float x, float y, float cirX, float cirY, float radius) {
	float xDis = cirX - x;
	float yDis = cirY - y;
	return (sqrt(xDis * xDis + yDis * yDis) < radius);
}

#define OFFSET_MAX	(25)

int main(int argc, char ** argv) { 
	int alpha = 1;
	int beta = 0;

	int xOffset = OFFSET_MAX;
	int yOffset = OFFSET_MAX;

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
	cap.set(CV_CAP_PROP_FRAME_WIDTH, 640);
	cap.set(CV_CAP_PROP_FRAME_HEIGHT, 480);

	if(!cap.isOpened()) {
		cout << "Capture could not be opened successfully" << endl;
		return -1;
	}

	namedWindow("Frame");
	namedWindow("Video");
	namedWindow("Control", CV_WINDOW_NORMAL);

	cvCreateTrackbar("minVelocityX", "Control", &minVelocityX, OFFSET_MAX);
	cvCreateTrackbar("minVelocityY", "Control", &minVelocityY, OFFSET_MAX);

	cvCreateTrackbar("alpha", "Control", &alpha, 32);
	cvCreateTrackbar("beta", "Control", &beta, 2048);

	cvCreateTrackbar("xOffset", "Control", &xOffset, OFFSET_MAX * 2);
	cvCreateTrackbar("yOffset", "Control", &yOffset, OFFSET_MAX * 2);

	while(char(waitKey(1)) != 'q' && cap.isOpened()) {
		static uint32_t shooting = 0;
		static uint32_t tracking = 0;

		uint32_t mainCircle = 0;
		float mainCircleDistance = numeric_limits<float>::max();
		static float trackingCircleDistance = numeric_limits<float>::max();

		Mat frame;
		Mat colors[3];
		Mat cimg;

		xCenter = WIDTH/2 + xOffset - OFFSET_MAX;
		yCenter = HEIGHT/2 + yOffset - OFFSET_MAX;

		vector<Vec3f> circles;

		cap >> frame;

		if(frame.empty()) {
			cout << "Video Over" << endl;
			break;
		}

		// Increase contrast and decrease brightness
		frame.convertTo(frame, -1, alpha, -beta);

		// Blur image for transform
		//medianBlur(frame, frame, blur);

		imshow("Frame", frame);

		cvtColor(frame, frame, CV_BGR2YCrCb);

		split(frame,colors);

		cimg = colors[2];

		// Convert to grayscale
		//cvtColor(frame, cimg, CV_BGR2GRAY);

		// Find some circles!
		HoughCircles(cimg, circles, CV_HOUGH_GRADIENT, 2, 32.0,
					 100, 30, MIN_RADIUS, MAX_RADIUS); // change the last two parameters
									// (min_radius & max_radius) to detect larger circles

		// Decrement shooting counter
		if(shooting > 0) {
			shooting--;
		}

		// Decrement tracking counter
		if(tracking > 0) {
			if(trackingCircleDistance < 1000) {
				circle( cimg, Point(xCenter, yCenter), trackingCircleDistance, Scalar(0,0,255), 1, CV_AA);
			}
			tracking--;
		} else {
			trackingCircleDistance = 1000;
		}

		// Figure out which detected circle is closest to the center
		for( size_t i = 0; i < circles.size(); i++ )
		{
			Vec3i c = circles[i];
			if(distanceFromCenter(c[0], c[1]) < mainCircleDistance) {
				mainCircle = i;
				mainCircleDistance = distanceFromCenter(c[0], c[1]);
			}
		}

		if(tracking && trackingCircleDistance < mainCircleDistance) {
			circles.clear();
		} else if(tracking && trackingCircleDistance > mainCircleDistance) {
			trackingCircleDistance = mainCircleDistance * 1.4;
			tracking = 20;
		} else if(!tracking) {
			trackingCircleDistance = mainCircleDistance * 1.4;
			tracking = 10;
		}

		if(trackingCircleDistance < 20) {
			trackingCircleDistance = 20;
		}

		if(circles.size()) {
			Vec3i c = circles[mainCircle];
			
			cout << "x:" << c[0] << " y:" << c[1] << " deviation: " << (xCenter - c[0]) << endl;
			
			if(isInCircle(c[0], c[1], xCenter, yCenter, c[2]/1.5)) {	
				controlfile << "laser 1\n" << endl;
				cout << "shoot!" << endl;
				
				shooting = 10; // Will shoot for the next 10 frames (to reduce glitches)
			} else {
				if(shooting == 0) {
					controlfile << "laser 0\n" << endl;
				}
				
				// Only move if not centered
				if((c[0] < (xCenter - c[2]/1.5)) || (c[0] > (xCenter + c[2]/1.5))) {
					moveX(xCenter - c[0]);
				} else {
					// Stop moving (only for gearmotors!)
					moveX(0);
				}
				
				// Only move if not centered
				if((c[1] < (yCenter - c[2]/1.5)) || (c[1] > (yCenter + c[2]/1.5))) {
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

			// Only turn off laser after a few frames without seeing the circle
			// This reduces glitches (will need a better system for multiple circles)
			if(shooting == 0) {
				controlfile << "laser 0\n" << endl;
			}
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
