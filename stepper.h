#ifndef __STEPPER_H__
#define __STEPPER_H__

#include <stdint.h>

#define TOTAL_STEPPERS	(2)

void stepperInit();
void stepperSetDirection(uint8_t stepperId, uint8_t direction);
void stepperSetSpeed(uint8_t stepperId, uint16_t speed);
void stepperMove(uint8_t stepperId, uint16_t steps);
void stepperSetStepSize(uint8_t stepperId, uint16_t stepSize);
void stepperCenter(uint8_t stepperId);
void stepperSetBounds(uint8_t stepperId, int16_t lBound, int16_t uBound);
void stepperGetBounds(uint8_t stepperId, int16_t *lBound, int16_t *uBound);
int16_t stepperGetPosition(uint8_t stepperId);
void stepperSetPosition(uint8_t stepperId, int16_t position, uint16_t speed);
void stepperEnable(uint8_t stepperId);
void stepperDisable(uint8_t stepperId);

// TODO
// void stepperSetMicrostep(uint8_t stepperId, uint8_t stepMode);

#endif
