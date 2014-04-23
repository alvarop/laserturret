#ifndef __TARGET_H__
#define __TARGET_H__

#include <stdint.h>

#define TOTAL_TARGETS			(10)
#define TARGET_REFRESH_RATE		(50)
#define TARGET_HIT_THRESHOLD	(500)
#define TARGET_CAL_SAMPLES		(100)

void targetInit();
void targetStart();
void targetStop();
void targetCalibrate(uint8_t target, uint8_t state);
uint16_t targetGetHitThreshold(uint8_t target);
void targetSetHitThreshold(uint8_t target, uint16_t newThreshold);
void targetSet(uint8_t target, uint8_t enable);
uint16_t targetRead(uint8_t target);
void targetProcess();

#endif
