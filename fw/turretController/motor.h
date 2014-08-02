#ifndef __MOTOR_H__
#define __MOTOR_H__

#include <stdint.h>

#define TOTAL_MOTORS	(2)
#define PERIOD_MS		(10.0)

void motorInit();
void motorCenter();
void motorSetPos(uint8_t motor, int16_t pos);
int16_t motorGetPos(uint8_t motor);
void motorStop(uint8_t motor);
void motorProcess();

#endif
