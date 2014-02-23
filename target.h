#ifndef __TARGET_H__
#define __TARGET_H__

#include <stdint.h>

#define TOTAL_TARGETS			(1)
#define TARGET_REFRESH_RATE		(250)

void targetInit();
void targetCalibrate(uint8_t target, uint8_t state);
void targetSet(uint8_t target, uint8_t enable);
uint16_t targetGet(uint8_t target);
void targetProcess();

#endif
