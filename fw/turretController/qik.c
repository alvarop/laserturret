#include <stdio.h>
#include "qik.h"
#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"

void qikInit() {
	USART_InitTypeDef USART_InitStruct;
	// USART_ClockInitTypeDef USART_ClockInitStruct;

	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);

	GPIO_Init(GPIOA, &(GPIO_InitTypeDef){GPIO_Pin_2, GPIO_Mode_AF, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});
	GPIO_Init(GPIOA, &(GPIO_InitTypeDef){GPIO_Pin_3, GPIO_Mode_AF, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});

	GPIO_PinAFConfig(GPIOA, GPIO_PinSource2, GPIO_AF_USART2);
	GPIO_PinAFConfig(GPIOA, GPIO_PinSource3, GPIO_AF_USART2);

	USART_StructInit(&USART_InitStruct);
	// USART_ClockStructInit(&USART_ClockInitStruct);

	USART_InitStruct.USART_BaudRate = 38400;

	USART_Init(USART2, &USART_InitStruct);

	USART_Cmd(USART2, ENABLE);
}


