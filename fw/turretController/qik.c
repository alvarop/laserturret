#include <stdio.h>
#include "qik.h"
#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"

#define CMD_FLAG		(0x80)

#define CMD_GETFWVER	(0x81)
#define CMD_GETERR		(0x82)

#define CMD_GETPARAM	(0x83)
#define CMD_SETPARAM	(0x83)

#define CMD_M0COAST		(0x86)
#define CMD_M1COAST		(0x87)

#define CMD_M0FWD		(0x88)
#define CMD_M0FWD2		(0x89)
#define CMD_M0REV		(0x8A)
#define CMD_M0REV2		(0x8B)

#define CMD_M1FWD		(0x8C)
#define CMD_M1FWD2		(0x8D)
#define CMD_M1REV		(0x8E)
#define CMD_M1REV2		(0x8F)

#define CMD_DIFF		(CMD_M1FWD - CMD_M0FWD)

void qikInit() {
	USART_InitTypeDef USART_InitStruct;
	// USART_ClockInitTypeDef USART_ClockInitStruct;

	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOC, ENABLE);

	GPIO_Init(GPIOC, &(GPIO_InitTypeDef){GPIO_Pin_10, GPIO_Mode_AF, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});
	GPIO_Init(GPIOC, &(GPIO_InitTypeDef){GPIO_Pin_11, GPIO_Mode_AF, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});

	GPIO_PinAFConfig(GPIOC, GPIO_PinSource10, GPIO_AF_USART3);
	GPIO_PinAFConfig(GPIOC, GPIO_PinSource11, GPIO_AF_USART3);

	USART_StructInit(&USART_InitStruct);
	// USART_ClockStructInit(&USART_ClockInitStruct);

	USART_InitStruct.USART_BaudRate = 38400;

	USART_Init(USART3, &USART_InitStruct);

	USART_Cmd(USART3, ENABLE);

	// In case autobaud is on
	USART3->DR = 0xAA;
}

static inline void qikTxCmdWithParam(uint8_t cmd, uint8_t param) {
	while(!(USART3->SR & USART_FLAG_TXE));
	USART3->DR = cmd;
	while(!(USART3->SR & USART_FLAG_TXE));
	USART3->DR = param;
}

static inline void qikTxCmd(uint8_t cmd) {
	while(!(USART3->SR & USART_FLAG_TXE));
	USART3->DR = cmd;
}

void qikSetSpeed(uint8_t device, uint8_t speed, uint8_t direction) {
	uint8_t cmd;

	if(direction) {
		cmd = CMD_M0FWD;
	} else {
		cmd = CMD_M0REV;
	}

	if(device) {
		cmd += CMD_DIFF;
	}

	qikTxCmdWithParam(cmd, speed);
}

void qikSetCoast(uint8_t device) {
	uint8_t cmd = CMD_M0COAST;

	if(device) {
		cmd = CMD_M1COAST;
	}

	qikTxCmd(cmd);
}
