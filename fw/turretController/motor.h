#ifndef __MOTOR_H__
#define __MOTOR_H__

#include <stdint.h>

#define TOTAL_MOTORS	(2)
#define PERIOD_MS		(2.0)

typedef enum {
	pidP,
	pidI,
	pidD,
	pidNone
} pidVar_t;

void motorInit();
void motorCenter();
void motorDebug(uint8_t enabled);
void motorEnable();
void motorDisable();
void motorSetPIDVar(uint8_t motor, pidVar_t var, int32_t val);
void motorSetPos(uint8_t motor, int16_t pos);
int16_t motorGetPos(uint8_t motor);
void motorStop(uint8_t motor);
void motorProcess();

#endif
