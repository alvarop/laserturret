#include <stdio.h>
#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"
#include "motor.h"
#include "qdecoder.h"
#include "qik.h"

typedef struct {
	int16_t newPos;
	int16_t oldPos;
	int16_t maxPos;
	int16_t minPos;
	float kp;
	float kd;
	float ki;
	int16_t oldErr;
	float p;
	float d;
	float i;
} motor_t;

extern volatile uint32_t tickMs;

static motor_t motors[TOTAL_MOTORS];
static uint32_t nextUpdate;

static float sampleTime = (float)PERIOD_MS/1000.0;


void motorInit() {
	qikInit();
	qdecoderInit();

	for(uint8_t motor = 0; motor < TOTAL_MOTORS; motor++) {
		motors[motor].newPos = 0;
		motors[motor].oldPos = 0;
		motors[motor].maxPos = INT16_MAX;
		motors[motor].minPos = INT16_MIN;

		motors[motor].kp = 1.0;
		motors[motor].kd = 0.0;
		motors[motor].ki = 0.0;

		motors[motor].oldErr = 0;

		motors[motor].p = 0;
		motors[motor].d = 0;
		motors[motor].i = 0;

		qdecoderReset(motor);
		qikSetSpeed(motor, 0 , 0);
	}

	nextUpdate = tickMs += PERIOD_MS;
}

void motorCenter() {

}

void motorSetPos(uint8_t motor, int16_t pos) {
	if(motor < TOTAL_MOTORS) {
		if(pos < motors[motor].minPos) {
			pos = motors[motor].minPos;
		} 

		if(pos > motors[motor].maxPos) {
			pos = motors[motor].maxPos;
		}

		motors[motor].newPos = pos;
		printf("M%d = %d\n", motor, pos);
	}
}

void motorStop(uint8_t motor) {
	if(motor < TOTAL_MOTORS) {
		qikSetSpeed(motor, 0 , 0);
		motors[motor].newPos = motorGetPos(motor);
		motors[motor].oldPos = motors[motor].newPos;
		printf("Stop M%d\n", motor);
	}
}

int16_t motorGetPos(uint8_t motor) {
	int16_t pos = 0;
	
	if(motor < TOTAL_MOTORS) {
		pos = qdecoderGet(motor);
	}

	return pos;
}

void motorProcess() {
	if(tickMs > nextUpdate) {
		nextUpdate = tickMs + PERIOD_MS;
	
		for(uint8_t motor = 0; motor < TOTAL_MOTORS; motor++) {
			int32_t err = motors[motor].newPos - motorGetPos(motor);
			int16_t speed;

			motors[motor].oldErr = err;

			motors[motor].p = motors[motor].kp * (float)err;
			motors[motor].d = motors[motor].kd * (float)(err - motors[motor].oldErr)/sampleTime;
			motors[motor].i += motors[motor].ki * (float)err;

			speed = (int16_t)(motors[motor].p + motors[motor].d + motors[motor].i);

			// Saturate
			if(speed >= 0) {
				if(speed > 126) {
					speed = 126;
				}
				qikSetSpeed(motor, speed, 1);
			} else {
				if(speed < -126) {
					speed = -126;
				}
				qikSetSpeed(motor, -speed, 0);
			}
		}
	}
}
