#include <iostream>
#include <fstream>
#include <opencv2/opencv.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <stdlib.h>

using namespace std;
using namespace cv;

ofstream controlfile;

float xPos = 0.0f;
float yPos = 0.0f;

float xCenter;
float yCenter;

#define WIDTH (640)
#define HEIGHT (480)

#define MICROSTEP_16
#ifdef MICROSTEP_16
// This is for /16 microstepping
#define XMAX	(2400)
#define YMAX	(2000)
#define SPEED (1000)
#else
// This is for NO microstepping
#define XMAX	(150)
#define YMAX	(125)
#define SPEED	(2500)
#endif

void moveX(int32_t xDev) {
	uint32_t xServo;
	int32_t xStepper;
	int32_t xMov = 0;
	
	xPos = (float)xDev/WIDTH;
	
	if(xPos < -0.5) {
		xPos = -0.5;
		xMov = -20;
	} else if (xPos > 0.5) {
		xPos = 0.5;
		xMov = 20;
	}
	
	xStepper = -xPos * 2 * XMAX;
	
	xServo = 1500 + xPos * 1000;
	
	xMov -= xPos * 200;
	
	//controlfile << "servo 0 " << xServo << "\n" << endl;
	//controlfile << "stepper 0 pos " << xStepper << " " << SPEED << "\n" << endl;
	controlfile << "qik 0 mov " << xMov << "\n" << endl;
	cout << "qik 0 mov " << xMov << "\n" << endl;
}

void moveY(int32_t yDev) {
	uint32_t yServo;
	int32_t yStepper;
	int32_t yMov = 0;
	
	yPos = (float)yDev/HEIGHT;

	if(yPos < -0.5) {
		yPos = -0.5;
		yMov = 20;
	} else if (yPos > 0.5) {
		yPos = 0.5;
		yMov = -20;
	}
	
	yStepper = -yPos * 2 * YMAX;
	
	yServo = 1500 + yPos * 1000;
	
	yMov -= yPos * 200;

	//controlfile << "servo 1 " << yServo << "\n" << endl;

	//controlfile << "stepper 1 pos " << yStepper << " " << SPEED << "\n" << endl;
	//cout << "stepper 1 pos " << yStepper << " " << SPEED << "\n" << endl;

	controlfile << "qik 1 mov " << yMov << "\n" << endl;
	cout << "qik 1 mov " << yMov << " " << yPos << "\n" << endl;
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

	if(argc > 4) {
		xCenter += strtol(argv[3], NULL, 0);
		yCenter += strtol(argv[4], NULL, 0);
	}

	cout << "xCenter: " << xCenter << " yCenter: " << yCenter << endl; 

	controlfile.open(argv[1], ios::out);

	controlfile << "servo 0 1500\n" << endl;
	controlfile << "servo 1 1500\n" << endl;
	
	controlfile << "stepper 0 bounds " << -XMAX << " " << XMAX << "\n" << endl;
	controlfile << "stepper 1 bounds " << -YMAX << " " << YMAX << "\n" << endl;
	
	controlfile << "stepper 0 on\n" << endl;
	controlfile << "stepper 1 on\n" << endl;
	
	
	controlfile << "qik 0 mov 0\n" << endl;
	controlfile << "qik 1 mov 0\n" << endl;
	
	//controlfile << "qik 0 coast\n" << endl;
	//controlfile << "qik 1 coast\n" << endl;
	
	controlfile << "laser 0\n" << endl;

	VideoCapture cap(strtoul(argv[2], NULL, 10));

	if(!cap.isOpened()) {
		cout << "Capture could not be opened successfully" << endl;
		return -1;
	}

	namedWindow("Video");

	while(char(waitKey(1)) != 'q' && cap.isOpened()) {
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
					 100, 30, 5, 40 // change the last two parameters
									// (min_radius & max_radius) to detect larger circles
					 );
		uint32_t mainCircle = 0;
		uint32_t mainCircleDistance = 100000;
		
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
			
			circle( cimg, Point(c[0], c[1]), c[2], Scalar(0,0,255), 3, CV_AA);
			circle( cimg, Point(c[0], c[1]), 2, Scalar(0,255,0), 3, CV_AA);
		} else {
		
			controlfile << "qik 0 mov 0\n" << endl;
			controlfile << "qik 1 mov 0\n" << endl;
			//controlfile << "qik 0 coast\n" << endl;
			//controlfile << "qik 1 coast\n" << endl;
			controlfile << "laser 0\n" << endl;
		}
		
		

		imshow("Video", cimg);
	}

	controlfile << "stepper 0 off\n" << endl;
	controlfile << "stepper 1 off\n" << endl;
	
	controlfile << "servo 0 1500\n" << endl;
	controlfile << "servo 1 1500\n" << endl;
	controlfile << "laser 0\n" << endl;
	
	controlfile << "qik 0 mov 0\n" << endl;
	controlfile << "qik 1 mov 0\n" << endl;
	
	controlfile << "qik 0 coast\n" << endl;
	controlfile << "qik 1 coast\n" << endl;

	controlfile.close();

	return 0;
}
