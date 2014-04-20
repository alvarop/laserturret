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

typedef struct {
	GPIO_TypeDef *port;
	uint8_t lPin;
	uint8_t rPin;
	uint8_t dir;
	uint8_t lStop;
	uint8_t rStop;
} qikMotor_t;

static qikMotor_t m0 = {GPIOA, 0, 1, 0, 0, 0};
static qikMotor_t m1 = {GPIOA, 6, 7, 0, 0, 0};

void qikInit() {
	USART_InitTypeDef USART_InitStruct;
	// USART_ClockInitTypeDef USART_ClockInitStruct;

	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);

	GPIO_Init(m0.port, &(GPIO_InitTypeDef){(1 << m0.lPin), GPIO_Mode_IN, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_UP});
	GPIO_Init(m0.port, &(GPIO_InitTypeDef){(1 << m0.rPin), GPIO_Mode_IN, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_UP});

	GPIO_Init(m1.port, &(GPIO_InitTypeDef){(1 << m1.lPin), GPIO_Mode_IN, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_UP});
	GPIO_Init(m1.port, &(GPIO_InitTypeDef){(1 << m1.rPin), GPIO_Mode_IN, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_UP});

	GPIO_Init(GPIOA, &(GPIO_InitTypeDef){GPIO_Pin_2, GPIO_Mode_AF, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});
	GPIO_Init(GPIOA, &(GPIO_InitTypeDef){GPIO_Pin_3, GPIO_Mode_AF, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});

	GPIO_PinAFConfig(GPIOA, GPIO_PinSource2, GPIO_AF_USART2);
	GPIO_PinAFConfig(GPIOA, GPIO_PinSource3, GPIO_AF_USART2);

	USART_StructInit(&USART_InitStruct);
	// USART_ClockStructInit(&USART_ClockInitStruct);

	USART_InitStruct.USART_BaudRate = 38400;

	USART_Init(USART2, &USART_InitStruct);

	USART_Cmd(USART2, ENABLE);

	// In case autobaud is on
	USART2->DR = 0xAA;
}

static inline void qikTxCmdWithParam(uint8_t cmd, uint8_t param) {
	while(!(USART2->SR & USART_FLAG_TXE));
	USART2->DR = cmd;
	while(!(USART2->SR & USART_FLAG_TXE));
	USART2->DR = param;
}

static inline void qikTxCmd(uint8_t cmd) {
	while(!(USART2->SR & USART_FLAG_TXE));
	USART2->DR = cmd;
}

void qikSetSpeed(uint8_t device, uint8_t speed, uint8_t direction) {
	uint8_t cmd;

	if(direction) {
		cmd = CMD_M0FWD;
		if(device == 0) {m0.dir = 1;}
		if(device == 1) {m1.dir = 1;}
	} else {
		cmd = CMD_M0REV;
		if(device == 0) {m0.dir = 0;}
		if(device == 1) {m1.dir = 0;}
	}

	if(device) {
		cmd += CMD_DIFF;
	} else {
		m0.lStop = 0;
		m0.rStop = 0;
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


// TODO - use interrupts
void qikProcess() {
	
	if(GPIO_ReadInputDataBit(m0.port, (1 << m0.lPin)) == 0) {
		if(!m0.lStop) {
			if(m0.dir == 0) {
				qikSetSpeed(0, 0, 0);
			}
	
			puts("LSTOP!");
			m0.lStop = 1;
		}
	} else {
		m0.lStop = 0;
	}

	if(GPIO_ReadInputDataBit(m0.port, (1 << m0.rPin)) == 0) {
		if(!m0.rStop) {
			if(m0.dir == 1) {
				qikSetSpeed(0, 0, 0);
			}
	
			puts("RSTOP!");
			m0.rStop = 1;
		}
	} else {
		m0.rStop = 0;
	}

	if(GPIO_ReadInputDataBit(m1.port, (1 << m1.lPin)) == 0) {
		if(!m1.lStop) {
			if(m1.dir == 0) {
				qikSetSpeed(1, 0, 0);
			}
	
			puts("USTOP!");
			m1.lStop = 1;
		}
	} else {
		m1.lStop = 0;
	}

	if(GPIO_ReadInputDataBit(m1.port, (1 << m1.rPin)) == 0) {
		if(!m1.rStop) {
			if(m1.dir == 1) {
				qikSetSpeed(1, 0, 0);
			}
	
			puts("DSTOP!");
			m1.rStop = 1;
		}
	} else {
		m1.rStop = 0;
	}
}

