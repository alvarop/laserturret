#ifndef __SERVO_H__
#define __SERVO_H__

#include <stdint.h>

#define TOTAL_SERVOS	(2)

void servoInit();
void servoSetPosition(uint8_t servo, uint16_t position);

#endif
