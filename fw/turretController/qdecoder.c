#include "qdecoder.h"
#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"

static int16_t oldX;
static int16_t oldY;

void qdecoderInit() {

	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOC, ENABLE);
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM8, ENABLE);
	
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_100MHz;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_NOPULL;
	
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;
	GPIO_Init(GPIOC, &GPIO_InitStructure);
	
	GPIO_PinAFConfig(GPIOC, GPIO_PinSource6, GPIO_AF_TIM8);
	GPIO_PinAFConfig(GPIOC, GPIO_PinSource7, GPIO_AF_TIM8);

	TIM_TimeBaseInitTypeDef  TIM_TimeBaseStructure;
	TIM_TimeBaseStructure.TIM_Period = 0xffffffffff;
	TIM_TimeBaseStructure.TIM_Prescaler = 0;
	TIM_TimeBaseStructure.TIM_ClockDivision = 0;
	TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
	
	TIM_TimeBaseInit(TIM8, &TIM_TimeBaseStructure);
	
	/* Configure the timer */
	TIM_EncoderInterfaceConfig(TIM8, TIM_EncoderMode_TI12, TIM_ICPolarity_Rising, TIM_ICPolarity_Rising);
	
	/* TIM8 counter enable */
	TIM_Cmd(TIM8, ENABLE);


	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4, ENABLE);
	
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_100MHz;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_NOPULL;
	
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;
	GPIO_Init(GPIOB, &GPIO_InitStructure);
	
	GPIO_PinAFConfig(GPIOB, GPIO_PinSource6, GPIO_AF_TIM4);
	GPIO_PinAFConfig(GPIOB, GPIO_PinSource7, GPIO_AF_TIM4);
	
	TIM_TimeBaseStructure.TIM_Period = 0xffff;
	TIM_TimeBaseStructure.TIM_Prescaler = 0;
	TIM_TimeBaseStructure.TIM_ClockDivision = 0;
	TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
	
	TIM_TimeBaseInit(TIM4, &TIM_TimeBaseStructure);
	
	/* Configure the timer */
	TIM_EncoderInterfaceConfig(TIM4, TIM_EncoderMode_TI12, TIM_ICPolarity_Rising, TIM_ICPolarity_Rising);
	
	/* TIM4 counter enable */
	TIM_Cmd(TIM4, ENABLE);


}

void qdecoderReset() {


}

void qdecoderProcess() {
	int16_t newX = TIM_GetCounter(TIM8);
	int16_t newY = TIM_GetCounter(TIM4);
	int32_t newValue = 0;

	if(newX != oldX) {
		oldX = newX;
		newValue = 1;
	}

	if(newY != oldY) {
		oldY = newY;
		newValue = 1;
	}

	if(newValue) {
		printf("%d, %d\n", oldX, oldY);
	}

}
