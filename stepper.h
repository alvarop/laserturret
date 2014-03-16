#ifndef __STEPPER_H__
#define __STEPPER_H__

#include <stdint.h>

#define TOTAL_STEPPERS	(2)

void stepperInit();
void stepperSetDirection(uint8_t stepperId, uint8_t direction);
void stepperSetSpeed(uint8_t stepperId, uint16_t speed);
void stepperMove(uint8_t stepperId, uint16_t steps);
void stepperProcess();

#endif
