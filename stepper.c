#include <stdio.h>
#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"
#include "stepper.h"

extern volatile uint32_t tickMs;

typedef struct {
	GPIO_TypeDef* stepPort;
	GPIO_TypeDef* directionPort;
	uint8_t	stepPin;
	uint8_t	directionPin;
	uint8_t direction;
	uint8_t ccr;
	uint16_t speed;
	uint16_t stepsRemaining;
	uint16_t stepSize;
	uint16_t state;
	int32_t position;
} stepperMotor_t;

static TIM_TypeDef *stepTimer = TIM3;

static stepperMotor_t steppers[TOTAL_STEPPERS + 1] = {
	{GPIOB,		GPIOB,		0,		11,		0,		3,		10,		0,		750,	0,		0},
	{GPIOB,		GPIOB,		1,		12,		0,		4,		10,		0,		750,	0,		0},
	{NULL,		NULL,		0,		0,		0,		0,		0,		0,		750,	0,		0}
};

void stepperInit() {
 	TIM_TimeBaseInitTypeDef timerConfig;

	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);

	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);


	TIM_TimeBaseStructInit(&timerConfig);

	timerConfig.TIM_Prescaler = 84; // APB1 runs at 84MHz
	timerConfig.TIM_ClockDivision = 0;
	timerConfig.TIM_CounterMode = TIM_CounterMode_Up;

	TIM_TimeBaseInit(stepTimer, &timerConfig);

	// Enable the timer!
	TIM_Cmd(stepTimer, ENABLE);

	// Setup pins
	for(stepperMotor_t *stepper = steppers; stepper->stepPort != NULL; stepper++) {
		GPIO_Init(stepper->stepPort, &(GPIO_InitTypeDef){(1 << stepper->stepPin), GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
		GPIO_Init(stepper->directionPort, &(GPIO_InitTypeDef){(1 << stepper->directionPin), GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
	}

	NVIC_EnableIRQ(TIM3_IRQn);
}

void stepperSetDirection(uint8_t stepperId, uint8_t direction) {
	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];

		stepper->direction = direction;
		GPIO_WriteBit(stepper->directionPort, (1 << stepper->directionPin), direction);
	}
}

void stepperSetSpeed(uint8_t stepperId, uint16_t speed) {
	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];
		
		if(stepper->stepSize < speed) {
			stepper->speed = speed - stepper->stepSize;
		}
	}
}

void stepperMove(uint8_t stepperId, uint16_t steps) {
	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];
		volatile uint32_t *ccr = &stepTimer->CCR1 + (steppers->ccr - 1);

		stepper->stepsRemaining = steps;

		// Start moving
		*ccr = stepTimer->CNT + 1;
		stepTimer->DIER |= (1 << stepper->ccr);
	}
}

void TIM3_IRQHandler(void) {
	uint32_t sr = stepTimer->SR;

	stepTimer->SR = 0;

	for(stepperMotor_t *stepper = steppers; stepper->stepPort != NULL; stepper++) {
		if(sr & (1 << stepper->ccr)) {
			if(stepper->stepsRemaining) {
				volatile uint32_t *ccr = &stepTimer->CCR1 + (steppers->ccr - 1);
				
				if(stepper->state) {
					stepper->state = 0;
					*ccr += stepper->speed;
					GPIO_ResetBits(stepper->stepPort, (1 << stepper->stepPin));
				} else {
					stepper->state = 1;
					*ccr += stepper->stepSize;
					GPIO_SetBits(stepper->stepPort, (1 << stepper->stepPin));

					stepper->stepsRemaining--;

					if(stepper->direction) {
						stepper->position += 1;
					} else {
						stepper->position -= 1;
					}
				}
			} else {
				GPIO_ResetBits(stepper->stepPort, (1 << stepper->stepPin));
				stepTimer->DIER &= ~(1 << stepper->ccr);
				stepper->state = 0;
			}
		}
	}
}
