#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"
#include "servo.h"

#define SERVO_NEUTRAL	(1500)
#define SERVO_MIN		(1000)
#define SERVO_MAX		(2000)

uint16_t servoPosition[TOTAL_SERVOS];

void servoInit() {
	TIM_TimeBaseInitTypeDef timerConfig;
	TIM_OCInitTypeDef ocConfig;

	// GPIOE Periph clock enable
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOE, ENABLE);

	GPIO_PinAFConfig(GPIOE, GPIO_PinSource5, GPIO_AF_TIM9);
	GPIO_PinAFConfig(GPIOE, GPIO_PinSource6, GPIO_AF_TIM9);

	// Use PE5 and PE6 for servo control
	GPIO_Init(GPIOE, &(GPIO_InitTypeDef){GPIO_Pin_5, GPIO_Mode_AF, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
	GPIO_Init(GPIOE, &(GPIO_InitTypeDef){GPIO_Pin_6, GPIO_Mode_AF, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});

	// Power the timer
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM9, ENABLE);

	//
	// Configure timer for 10ms period and 1.5ms pulses (centered)
	//
	TIM_TimeBaseStructInit(&timerConfig);

	timerConfig.TIM_Period = 10000;
	timerConfig.TIM_Prescaler = 168;
	timerConfig.TIM_ClockDivision = 0;
	timerConfig.TIM_CounterMode = TIM_CounterMode_Up;

	TIM_TimeBaseInit(TIM9, &timerConfig);

	//
	// Configure output compare stuff
	//
	TIM_OCStructInit(&ocConfig);

	ocConfig.TIM_OCMode = TIM_OCMode_PWM1;
	ocConfig.TIM_OutputState = TIM_OutputState_Enable;
	ocConfig.TIM_Pulse = SERVO_NEUTRAL;
	ocConfig.TIM_OCPolarity = TIM_OCPolarity_High;

	TIM_OC1Init(TIM9, &ocConfig);
	TIM_OC2Init(TIM9, &ocConfig);

	TIM_ARRPreloadConfig(TIM9, ENABLE);

	// Enable the timer!
	TIM_Cmd(TIM9, ENABLE);

	for(uint8_t servo = 0; servo < TOTAL_SERVOS; servo++) {
		servoPosition[servo] = SERVO_NEUTRAL;
	}
}

void servoSetPosition(uint8_t servo, uint16_t position) {
	volatile uint32_t *ccr;

	if(position > SERVO_MAX) position = SERVO_MAX;
	if(position < SERVO_MIN) position = SERVO_MIN;

	if(servo < TOTAL_SERVOS) {
		ccr = (&TIM9->CCR1 + servo);
		*ccr = position;
	}

}
