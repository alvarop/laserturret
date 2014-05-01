#include <stdio.h>
#include "target.h"
#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"

typedef struct {
	GPIO_TypeDef* sensePort;
	uint8_t sensePin;
	ADC_TypeDef* adc;
	GPIO_TypeDef* powerPort;
	uint8_t powerPin;
	uint8_t adcChannel;
	uint8_t enabled;
	uint8_t connected;
	uint32_t timeHit;
	uint16_t hitThreshold;
	uint16_t lowThreshold;
	uint16_t highThreshold;
} target_t;

static target_t targets[TOTAL_TARGETS] = {
	{GPIOA,	0,	ADC1,	GPIOA,	15,	0,	0, 0, 0, 2048, 0, 4096},
	{GPIOA,	1,	ADC1,	GPIOB,	4,	1,	0, 0, 0, 2048, 0, 4096},
	{GPIOA,	2,	ADC1,	GPIOB,	5,	2,	0, 0, 0, 2048, 0, 4096},
	{GPIOA,	3,	ADC1,	GPIOB,	7,	3,	0, 0, 0, 2048, 0, 4096},

	{GPIOB,	0,	ADC1,	GPIOB,	8,	8,	0, 0, 0, 2048, 0, 4096},
	{GPIOB,	1,	ADC1,	GPIOB,	11,	9,	0, 0, 0, 2048, 0, 4096},

	{GPIOC,	1,	ADC1,	GPIOB,	12,	11,	0, 0, 0, 2048, 0, 4096},
	{GPIOC,	2,	ADC1,	GPIOB,	13,	12,	0, 0, 0, 2048, 0, 4096},
	{GPIOC,	4,	ADC1,	GPIOB,	14,	13,	0, 0, 0, 2048, 0, 4096},
	{GPIOC,	5,	ADC1,	GPIOC,	6,	15,	0, 0, 0, 2048, 0, 4096},
	
};

extern volatile uint32_t tickMs;
static uint32_t targetTimer;
static uint8_t targetsRunning;

#define PORT_LETTER(x) (((((uint32_t)x) >> 10) & 0xF) + 'A')

void delay(uint32_t delay) {
	while(delay--) {
		asm volatile(" nop");
	}
}

void targetStart(uint8_t all) {
	targetsRunning = 1;

	if(all) {
		for(uint8_t target = 0; target < TOTAL_TARGETS; target++) {
			targetSet(target, 1);
		}
	}

	targetTimer = tickMs + TARGET_REFRESH_RATE;

	printf("targets started\n");

}

void targetStop() {
	targetsRunning = 0;
	printf("targets stopped\n");
}

void targetInit() {
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOC, ENABLE);

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1, ENABLE); 

	ADC_InitTypeDef adcConfig;

	ADC_DeInit();

	ADC_StructInit(&adcConfig);

	ADC_Init(ADC1, &adcConfig);

	ADC_Cmd(ADC1, ENABLE);

	for(uint8_t target = 0; target < TOTAL_TARGETS; target++) {
		GPIO_Init(targets[target].sensePort, &(GPIO_InitTypeDef){(1 << targets[target].sensePin), GPIO_Mode_AN, GPIO_OType_OD, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
		GPIO_Init(targets[target].powerPort, &(GPIO_InitTypeDef){(1 << targets[target].powerPin), GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});

		// Disable target
		GPIO_WriteBit(targets[target].powerPort, (1 << targets[target].powerPin), 1);

		// Wait for change to take effect
		delay(1000);

		// Check if target is plugged in
		if(targetRead(target) == 0xFFF) {
			printf("%d connected\n", target);
			targets[target].connected = 1;
		} else {
			targets[target].connected = 0;
		}

		// Enable target
		GPIO_WriteBit(targets[target].powerPort, (1 << targets[target].powerPin), 0);
	}

	targetTimer = 0;

	targetsRunning = 0;
}

uint16_t targetRead(uint8_t target) {
	uint16_t rval = 0;

	if(target < TOTAL_TARGETS) {
		ADC_RegularChannelConfig(targets[target].adc, targets[target].adcChannel, 1, ADC_SampleTime_144Cycles);
		ADC_SoftwareStartConv(targets[target].adc);
		while(ADC_GetFlagStatus(targets[target].adc, ADC_FLAG_EOC) == RESET){
			// do nothing
		}
		rval = ADC_GetConversionValue(targets[target].adc);
	}

	return rval;
}

void targetCalibrate(uint8_t target, uint8_t state) {
	if(target < TOTAL_TARGETS) {
		uint32_t samples = 0;

		//printf("Calibrating target %d.\nTaking %d samples\n", target, TARGET_CAL_SAMPLES);
		for(uint16_t sample = 0; sample < TARGET_CAL_SAMPLES; sample++) {
			uint16_t value = targetRead(target);
			samples += value;
			//printf("rd - %d\n", value);
		}

		// Get average
		samples /= TARGET_CAL_SAMPLES;

		//printf("Average value: %ld\n", samples);

		if(state) {
			targets[target].highThreshold = samples;
		} else {
			targets[target].lowThreshold = samples;
		}

		targets[target].hitThreshold = (targets[target].highThreshold - targets[target].lowThreshold)/2 + targets[target].lowThreshold;

		//printf("New hitThreshold = %d\n", targets[target].hitThreshold);
		printf("%d AVG %ld\n", target, samples);
	}
}

uint16_t targetGetHitThreshold(uint8_t target) {
	uint16_t hitThreshold = 0;

	if(target < TOTAL_TARGETS) {
		hitThreshold = targets[target].hitThreshold;
	}

	return hitThreshold;
}

void targetSetHitThreshold(uint8_t target, uint16_t newThreshold) {
	if(target < TOTAL_TARGETS) {
		targets[target].hitThreshold = newThreshold;
	}
}


void targetSet(uint8_t target, uint8_t enable) {
	if(target < TOTAL_TARGETS) {
		if(targets[target].connected) {	
			// Enable target
			GPIO_WriteBit(targets[target].powerPort, (1 << targets[target].powerPin), (~enable & 1));

			targets[target].enabled = enable;

			if(enable) {
				targets[target].timeHit = 0;
			}
		}
	}
}

void targetProcess() {
	//
	// WARNING - Not overflow safe!
	//
	if(targetsRunning && (targetTimer < tickMs)) {
		targetTimer = tickMs + TARGET_REFRESH_RATE;
		for(uint8_t target = 0; target < TOTAL_TARGETS; target++) {
			uint16_t currentValue = targetRead(target);
			if(currentValue > targets[target].hitThreshold) {
				targets[target].timeHit += TARGET_REFRESH_RATE;
			} else {
				if(targets[target].timeHit > (TARGET_REFRESH_RATE - 1)) {
					targets[target].timeHit -= TARGET_REFRESH_RATE;
				}
			}

			if(targets[target].enabled && (targets[target].timeHit >= TARGET_HIT_THRESHOLD)) {
				printf("%d hit\n", target);
				targetSet(target, 0); // Turn off the target
			}
		}
	}
}

