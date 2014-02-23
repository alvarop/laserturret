#include <stdio.h>
#include "target.h"
#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"

typedef struct {
	GPIO_TypeDef* port;
	uint8_t pin;
	ADC_TypeDef* adc;
	uint8_t adcChannel;
	uint32_t timeHit;
	uint16_t hitThreshold;
} target_t;

target_t targets[TOTAL_TARGETS] = {
	{GPIOA,	1,	ADC1,	1,	0, 8192}
};

extern volatile uint32_t tickMs;
uint32_t targetTimer;

void targetInit() {
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1, ENABLE); 

	ADC_InitTypeDef adcConfig;

	ADC_DeInit();

	ADC_StructInit(&adcConfig);

	ADC_Init(ADC1, &adcConfig);

	ADC_Cmd(ADC1, ENABLE);

	for(uint8_t target = 0; target < TOTAL_TARGETS; target++) {
		GPIO_Init(targets[target].port, &(GPIO_InitTypeDef){(1 << targets[target].pin), GPIO_Mode_AN, GPIO_OType_OD, GPIO_Speed_50MHz, GPIO_PuPd_NOPULL});
	}

	targetTimer = tickMs + TARGET_REFRESH_RATE;

}

uint16_t targetGet(uint8_t target) {
	uint16_t rval = 0;

	if(target < TOTAL_TARGETS) {
		ADC_RegularChannelConfig(targets[target].adc, targets[target].adcChannel, 1, ADC_SampleTime_56Cycles);
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

	}
}

void targetSet(uint8_t target, uint8_t enable) {
	if(target < TOTAL_TARGETS) {
		
	}
}

void targetProcess() {
	//
	// WARNING - Not overflow safe!
	//
	if(targetTimer < tickMs) {
		targetTimer = tickMs + TARGET_REFRESH_RATE;
		for(uint8_t target = 0; target < TOTAL_TARGETS; target++) {
			uint16_t currentValue = targetGet(target);
			printf("Target %d: %d\n", target, currentValue);
			if(currentValue > targets[target].hitThreshold) {
				targets[target].timeHit += TARGET_REFRESH_RATE;
			} else {
				if(target > (TARGET_REFRESH_RATE - 1)) {
					targets[target].timeHit -= TARGET_REFRESH_RATE;
				}
			}
		}
	}
}

