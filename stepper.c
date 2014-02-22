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
	uint16_t speed;
	uint32_t stepsRemaining;
	uint32_t nextStep;
} stepperMotor_t;

stepperMotor_t steppers[TOTAL_STEPPERS] = {
	{GPIOB,		GPIOB,		0,		11,		0, 		10, 	0,		0},
	{GPIOB,		GPIOB,		1,		12,		0, 		10, 	0,		0}
};

void stepperInit() {
// 	TIM_TimeBaseInitTypeDef timerConfig;
// 	TIM_OCInitTypeDef ocConfig;

// 	// GPIOE Periph clock enable
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);

// 	GPIO_PinAFConfig(GPIOB, GPIO_PinSource0, GPIO_AF_TIM3);
// 	GPIO_PinAFConfig(GPIOB, GPIO_PinSource1, GPIO_AF_TIM3);

// 	// Use PE5 and PE6 for servo control
// 	GPIO_Init(GPIOE, &(GPIO_InitTypeDef){GPIO_Pin_0, GPIO_Mode_AF, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
// 	GPIO_Init(GPIOE, &(GPIO_InitTypeDef){GPIO_Pin_1, GPIO_Mode_AF, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});

// 	// Power the timer
// 	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);

// 	//
// 	// Configure timer for 10ms period and 1.5ms pulses (centered)
// 	//
// 	TIM_TimeBaseStructInit(&timerConfig);

// 	timerConfig.TIM_Period = 10000;
// 	timerConfig.TIM_Prescaler = 168;
// 	timerConfig.TIM_ClockDivision = 0;
// 	timerConfig.TIM_CounterMode = TIM_CounterMode_Up;

// 	TIM_TimeBaseInit(TIM3, &timerConfig);

// 	// Enable the timer!
// 	TIM_Cmd(TIM3, ENABLE);

	// Setup pins
	for(uint8_t stepper = 0; stepper < TOTAL_STEPPERS; stepper++) {
		GPIO_Init(steppers[stepper].stepPort, &(GPIO_InitTypeDef){(1 << steppers[stepper].stepPin), GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
		GPIO_Init(steppers[stepper].directionPort, &(GPIO_InitTypeDef){(1 << steppers[stepper].directionPin), GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
	}
	// Step pins
//	GPIO_Init(GPIOB, &(GPIO_InitTypeDef){GPIO_Pin_0, GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
//	GPIO_Init(GPIOB, &(GPIO_InitTypeDef){GPIO_Pin_1, GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});

	// Direction pins
//	GPIO_Init(GPIOB, &(GPIO_InitTypeDef){GPIO_Pin_11, GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
//	GPIO_Init(GPIOB, &(GPIO_InitTypeDef){GPIO_Pin_12, GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
}

void stepperSetDirection(uint8_t stepper, uint8_t direction) {
	if(stepper < TOTAL_STEPPERS) {
		steppers[stepper].direction = direction;
		GPIO_WriteBit(steppers[stepper].directionPort, (1 << steppers[stepper].directionPin), direction);
	}
}

void stepperSetSpeed(uint8_t stepper, uint16_t speed) {
	if(stepper < TOTAL_STEPPERS) {
		steppers[stepper].speed = speed;
	}
}

void stepperMove(uint8_t stepper, uint16_t steps) {
	if(stepper < TOTAL_STEPPERS) {
		steppers[stepper].stepsRemaining = steps;
		steppers[stepper].nextStep = tickMs + steppers[stepper].speed;
	}
}

void delay(uint32_t delay) {
	while(delay--) {
		asm volatile(" nop");
	}
}

void stepperProcess() {
	for(uint8_t stepper = 0; stepper < TOTAL_STEPPERS; stepper++) {
		//
		// WARNING - Timer code does not check for uint32_t overflow!
		//
		if(steppers[stepper].stepsRemaining && (steppers[stepper].nextStep < tickMs)) {
			steppers[stepper].nextStep = tickMs + steppers[stepper].speed;
			steppers[stepper].stepsRemaining--;
			
			GPIO_SetBits(steppers[stepper].stepPort, (1 << steppers[stepper].stepPin));
			delay(31500); // ~750 ms
			GPIO_ResetBits(steppers[stepper].stepPort, (1 << steppers[stepper].stepPin));
		}
	}
}
