#include <stdio.h>
#include <stdint.h>

#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"

#include "usbd_core.h"
#include "usbd_usr.h"
#include "usbd_desc.h"
#include "usbd_cdc_vcp.h"

#include "console.h"
#include "galvo.h"

#define BLINK_DELAY_MS	(500)

volatile uint32_t tickMs = 0;
__ALIGN_BEGIN USB_OTG_CORE_HANDLE  USB_OTG_dev __ALIGN_END;

// Private function prototypes
void Delay(volatile uint32_t nCount);
void init();

static const uint16_t sinLUT[256] = {2048, 2098, 2148, 2198, 2248, 2298, 2348, 2398, 2447, 2496, 2545, 2594, 2642, 2690, 2737, 2785, 2831, 2877, 2923, 2968, 3013, 3057, 3100, 3143, 3185, 3227, 3267, 3307, 3347, 3385, 3423, 3460, 3496, 3531, 3565, 3598, 3631, 3662, 3692, 3722, 3750, 3778, 3804, 3829, 3854, 3877, 3899, 3920, 3940, 3958, 3976, 3992, 4007, 4021, 4034, 4046, 4056, 4065, 4073, 4080, 4086, 4090, 4093, 4095, 4096, 4095, 4093, 4090, 4086, 4080, 4073, 4065, 4056, 4046, 4034, 4021, 4007, 3992, 3976, 3958, 3940, 3920, 3899, 3877, 3854, 3829, 3804, 3778, 3750, 3722, 3692, 3662, 3631, 3598, 3565, 3531, 3496, 3460, 3423, 3385, 3347, 3307, 3267, 3227, 3185, 3143, 3100, 3057, 3013, 2968, 2923, 2877, 2831, 2785, 2737, 2690, 2642, 2594, 2545, 2496, 2447, 2398, 2348, 2298, 2248, 2198, 2148, 2098, 2048, 1997, 1947, 1897, 1847, 1797, 1747, 1697, 1648, 1599, 1550, 1501, 1453, 1405, 1358, 1310, 1264, 1218, 1172, 1127, 1082, 1038, 995, 952, 910, 868, 828, 788, 748, 710, 672, 635, 599, 564, 530, 497, 464, 433, 403, 373, 345, 317, 291, 266, 241, 218, 196, 175, 155, 137, 119, 103, 88, 74, 61, 49, 39, 30, 22, 15, 9, 5, 2, 0, 0, 0, 2, 5, 9, 15, 22, 30, 39, 49, 61, 74, 88, 103, 119, 137, 155, 175, 196, 218, 241, 266, 291, 317, 345, 373, 403, 433, 464, 497, 530, 564, 599, 635, 672, 710, 748, 788, 828, 868, 910, 952, 995, 1038, 1082, 1127, 1172, 1218, 1264, 1310, 1358, 1405, 1453, 1501, 1550, 1599, 1648, 1697, 1747, 1797, 1847, 1897, 1947, 1997};

#define XOFFMAX (500)
#define XOFFMIN (-50)
#define YOFFMAX (500)
#define YOFFMIN (-50)

static int16_t xOff, yOff;
static int8_t xSpd, ySpd;

void controlLoopInit() {
	xSpd = 20;
	ySpd = -24;

	TIM_TimeBaseInitTypeDef timerConfig;

	// Power the timer
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM9, ENABLE);

	//
	// Configure timer for 100us period
	//
	TIM_TimeBaseStructInit(&timerConfig);

	timerConfig.TIM_Period = 50;
	timerConfig.TIM_Prescaler = 168;
	timerConfig.TIM_ClockDivision = 0;
	timerConfig.TIM_CounterMode = TIM_CounterMode_Up;

	TIM_TimeBaseInit(TIM9, &timerConfig);

	TIM_ITConfig(TIM9, TIM_IT_Update, ENABLE);

	NVIC_EnableIRQ(TIM1_BRK_TIM9_IRQn);

	// Enable the timer!
	TIM_Cmd(TIM9, ENABLE);
}



void TIM1_BRK_TIM9_IRQHandler(void) {
	uint32_t sr = TIM9->SR;
	TIM9->SR &= ~sr;

	static uint16_t x,y;

	if(sr & TIM_FLAG_Update) {
		GPIO_ToggleBits(GPIOD, GPIO_Pin_14);
		galvoSet(0, sinLUT[x]/32 + 256 + xOff);
		galvoSet(1, sinLUT[(y + 64) & 0xFF]/32 + 256 + yOff);

		x += 1;
		y += 1;

		x &= 0xFF;
		y &= 0xFF;


		
	}
}

#define MOVE_DELAY_MS (33)

int main(void) {
	uint32_t nextBlink;
	uint32_t nextMove;

	uint32_t blinkState = 0;
	init();

	// Disable line buffering on stdout
	setbuf(stdout, NULL);

	nextBlink = tickMs + BLINK_DELAY_MS;
	nextMove = tickMs + MOVE_DELAY_MS;
	for(;;) {

		consoleProcess();

		if(tickMs > nextBlink) {
			nextBlink = tickMs + BLINK_DELAY_MS;
			if(blinkState) {
				GPIO_SetBits(GPIOD, GPIO_Pin_12);
			} else {
				GPIO_ResetBits(GPIOD, GPIO_Pin_12);
			}
			blinkState ^= 1;
		}

		if(tickMs > nextMove) {
			nextMove = tickMs + MOVE_DELAY_MS;
			
			xOff += xSpd;
			if(xOff >= XOFFMAX) {
				xOff = XOFFMAX;
				xSpd = -xSpd;
			} else if(xOff <= XOFFMIN) {
				xOff = XOFFMIN;
				xSpd = -xSpd;
			}

			yOff += ySpd;
			if(yOff >= YOFFMAX) {
				yOff = YOFFMAX;
				ySpd = -ySpd;
			} else if(yOff <= YOFFMIN) {
				yOff = YOFFMIN;
				ySpd = -ySpd;
			}

		}

		__WFI();
		
	}

	return 0;
}

void init() {

	// ---------- SysTick timer -------- //
	if (SysTick_Config(SystemCoreClock / 1000)) {
		// Capture error
		while (1){};
	}

	// ---------- GPIO -------- //
	// GPIOD Periph clock enable
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOD, ENABLE);

	GPIO_Init(GPIOD, &(GPIO_InitTypeDef){GPIO_Pin_12, GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});
	GPIO_Init(GPIOD, &(GPIO_InitTypeDef){GPIO_Pin_14, GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});

	consoleInit();

	USBD_Init(&USB_OTG_dev,
				USB_OTG_FS_CORE_ID,
				&USR_desc,
				&USBD_CDC_cb,
				&USR_cb);

	controlLoopInit();
}

void SysTick_Handler(void)
{
	tickMs++;
}
