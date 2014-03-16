#include <iostream>
#include <fstream>
#include <opencv2/opencv.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>

using namespace std;
using namespace cv;

ofstream controlfile;

float xPos = 0.0f;
float yPos = 0.0f;

#define WIDTH (640)
#define HEIGHT (480)

#ifdef MICROSTEP_16
// This is for /16 microstepping
#define XMAX	(150)
#define YMAX	(100)
#define SPEED	(2500)
#else
// This is for /16 microstepping
#define XMAX	(2400)
#define YMAX	(1600)
#define SPEED (1000)
#endif

void moveX(int32_t xDev) {
	uint32_t xServo;
	int32_t xStepper;
	
	xPos += (float)xDev/WIDTH/5;
	
	if(xPos < -0.5) {
		xPos = -0.5;
	} else if (xPos > 0.5) {
		xPos = 0.5;
	}
	
	xStepper = -xPos * 2 * XMAX;
	
	xServo = 1500 + xPos * 1000;
	
	//controlfile << "servo 0 " << xServo << "\n" << endl;
	controlfile << "stepper 0 pos " << xStepper << " " << SPEED << "\n" << endl;
	cout << "stepper 0 pos " << xStepper << " " << SPEED << "\n" << endl;
}

void moveY(int32_t yDev) {
	uint32_t yServo;
	int32_t yStepper;
	
	yPos -= (float)yDev/HEIGHT/8;

	if(yPos < -0.5) {
		yPos = -0.5;
	} else if (yPos > 0.5) {
		yPos = 0.5;
	}
	
	yStepper = -yPos * 2 * YMAX;
	
	yServo = 1500 + yPos * 1000;

	//controlfile << "servo 1 " << yServo << "\n" << endl;

	controlfile << "stepper 1 pos " << yStepper << " " << SPEED << "\n" << endl;
	cout << "stepper 1 pos " << yStepper << " " << SPEED << "\n" << endl;
}

int main(int argc, char ** argv) { 
	
	if(argc < 2) {
		cout << "Need device name!" << endl;
		return -1;
	}

	controlfile.open(argv[1], ios::out);

	controlfile << "servo 0 1500\n" << endl;
	controlfile << "servo 1 1500\n" << endl;
	
	controlfile << "stepper 0 bounds " << -XMAX << " " << XMAX << "\n" << endl;
	controlfile << "stepper 1 bounds " << -YMAX << " " << YMAX << "\n" << endl;
	
	controlfile << "stepper 0 on\n" << endl;
	controlfile << "stepper 1 on\n" << endl;
	
	controlfile << "laser 0\n" << endl;

	VideoCapture cap(1);

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
					 100, 30, 10, 40 // change the last two parameters
									// (min_radius & max_radius) to detect larger circles
					 );
		uint32_t mainCircle = 0;
		uint32_t mainCircleRadius = 0;
		for( size_t i = 0; i < circles.size(); i++ )
		{
			Vec3i c = circles[i];
			if(c[2] > mainCircleRadius) {
				mainCircle = i;
				mainCircleRadius = c[2];
			}
		}

		if(circles.size()) {
			Vec3i c = circles[mainCircle];
			cout << "x:" << c[0] << " y:" << c[1] << " deviation: " << (WIDTH/2 - c[0]) << endl;
			if((c[0] > (WIDTH/2 - c[2])) && (c[0] < (WIDTH/2 + c[2]))
				&& (c[1] > (HEIGHT/2 - c[2])) && (c[1] < (HEIGHT/2 + c[2]))) {
				controlfile << "laser 1\n" << endl;
				cout << "shoot!" << endl;
			} else {
				controlfile << "laser 0\n" << endl;
				
				// Only move if not centered
				if((c[0] < (WIDTH/2 - c[2])) || (c[0] > (WIDTH/2 + c[2]))) {
					moveX(WIDTH/2 - c[0]);
				}
				
				// Only move if not centered
				if((c[1] < (HEIGHT/2 - c[2])) || (c[1] > (HEIGHT/2 + c[2]))) {
					moveY((HEIGHT/2 - c[1]));
				}
			}
			
			circle( cimg, Point(c[0], c[1]), c[2], Scalar(0,0,255), 3, CV_AA);
			circle( cimg, Point(c[0], c[1]), 2, Scalar(0,255,0), 3, CV_AA);
		} else {
			controlfile << "laser 0\n" << endl;
		}
		
		

		imshow("Video", cimg);
	}

	controlfile << "stepper 0 off\n" << endl;
	controlfile << "stepper 1 off\n" << endl;
	
	controlfile << "servo 0 1500\n" << endl;
	controlfile << "servo 1 1500\n" << endl;
	controlfile << "laser 0\n" << endl;

	controlfile.close();

	return 0;
}
