#include <stdio.h>
#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"
#include "stepper.h"

extern volatile uint32_t tickMs;

typedef struct {
	GPIO_TypeDef* stepPort;
	GPIO_TypeDef* directionPort;
	GPIO_TypeDef* enablePort;
	uint8_t	stepPin;
	uint8_t	directionPin;
	uint8_t	enablePin;
	uint8_t direction;
	uint8_t ccr;
	volatile uint16_t speed;
	volatile uint16_t stepsRemaining;
	volatile uint16_t stepSize;
	volatile uint16_t state;
	volatile int32_t position;
	int16_t lBound;
	int16_t uBound;
} stepperMotor_t;

static TIM_TypeDef *stepTimer = TIM3;

static stepperMotor_t steppers[TOTAL_STEPPERS + 1] = {
	{GPIOB,	GPIOB,	GPIOB,	0,	11,	13,	0,	3,	10,	0,	750,	0,	0,	INT16_MIN,	INT16_MAX},
	{GPIOB,	GPIOB,	GPIOB,	1,	12,	14,	0,	4,	10,	0,	750,	0,	0,	INT16_MIN,	INT16_MAX},
	{NULL,	NULL,	GPIOB,	0,	0,	0,	0,	0,	0,	0,	750,	0,	0,	INT16_MIN,	INT16_MAX}
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
		GPIO_Init(stepper->directionPort, &(GPIO_InitTypeDef){(1 << stepper->directionPin), GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});
		GPIO_Init(stepper->enablePort, &(GPIO_InitTypeDef){(1 << stepper->enablePin), GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});

		// Start disabled
		GPIO_SetBits(stepper->enablePort, (1 << stepper->enablePin));
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
		volatile uint32_t *ccr = &stepTimer->CCR1 + (stepper->ccr - 1);
		
		__disable_irq();

		if(stepper->direction) {
			if((stepper->position + steps) > stepper->uBound) {
				steps = stepper->uBound - stepper->position;
			}
		} else {
			if((stepper->position - steps) < stepper->lBound) {
				steps = stepper->position - stepper->lBound;
			}
		}

		stepper->stepsRemaining = steps;

		// Only schedule if stepper isn't already active
		if((stepTimer->DIER & (1 << stepper->ccr)) == 0) {
			*ccr = stepTimer->CNT;
		}

		stepTimer->DIER |= (1 << stepper->ccr);
		__enable_irq();
	}
}

void stepperSetStepSize(uint8_t stepperId, uint16_t stepSize) {
	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];
		stepper->stepSize = stepSize;
	}
}

void stepperCenter(uint8_t stepperId) {
	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];
		stepper->position = 0;
	}
}

void stepperSetBounds(uint8_t stepperId, int16_t lBound, int16_t uBound) {
	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];
		stepper->lBound = lBound;
		stepper->uBound = uBound;
	}
}

void stepperGetBounds(uint8_t stepperId, int16_t *lBound, int16_t *uBound) {
	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];
		*lBound = stepper->lBound;
		*uBound = stepper->uBound;
	}
}


int16_t stepperGetPosition(uint8_t stepperId) {
	int16_t position = 0;

	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];

		position = stepper->position;
	}

	return position;
}

void stepperSetPosition(uint8_t stepperId, int16_t position, uint16_t speed) {
	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];
		uint16_t steps = 0;

		__disable_irq();
		stepper->speed = speed - stepper->stepSize;

		if(position > stepper->position) {
			stepperSetDirection(stepperId, 1);

			steps = position - stepper->position;
			
		} else if(position < stepper->position) {
			stepperSetDirection(stepperId, 0);

			steps = stepper->position - position;
		}
		__enable_irq();

		if(steps) {
			stepperMove(stepperId, steps);
		}
	}
}

void stepperEnable(uint8_t stepperId){
	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];
		GPIO_ResetBits(stepper->enablePort, (1 << stepper->enablePin));
		printf("Stepper %d ON\n", stepperId);
	}
}

void stepperDisable(uint8_t stepperId){
	if(stepperId < TOTAL_STEPPERS) {
		stepperMotor_t *stepper = &steppers[stepperId];
		GPIO_SetBits(stepper->enablePort, (1 << stepper->enablePin));
		printf("Stepper %d OFF\n", stepperId);
	}
}

void TIM3_IRQHandler(void) {
	uint32_t sr = stepTimer->SR;

	stepTimer->SR = 0;

	for(stepperMotor_t *stepper = steppers; stepper->stepPort != NULL; stepper++) {
		if(sr & (1 << stepper->ccr)) {
			if(stepper->stepsRemaining) {
				volatile uint32_t *ccr = &stepTimer->CCR1 + (stepper->ccr - 1);
				
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
