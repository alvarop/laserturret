#ifndef __QIK_H__
#define __QIK_H__

#include <stdint.h>

void qikInit();
void qikSetSpeed(uint8_t device, uint8_t speed, uint8_t direction);
void qikSetCoast(uint8_t device);
void qikProcess();

#endif
