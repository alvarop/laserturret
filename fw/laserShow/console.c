#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "console.h"
#include "fifo.h"
#include "galvo.h"

#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"

typedef struct {
	char *commandStr;
	void (*fn)(uint8_t argc, char *argv[]);
	char *helpStr;
} command_t;

fifo_t usbRxFifo;

static char cmdBuff[64];
static uint8_t argc;
static char* argv[8];

static void helpFn(uint8_t argc, char *argv[]);
static void galvoFn(uint8_t argc, char *argv[]);

static command_t commands[] = {
	// Add new commands here!
	// {"g", galvoFn,	"Usage: g <galvo(0-1)> <pos(-32767-32767)"},
	{"help", helpFn, "Print this!"},
	{NULL, NULL, NULL}
};

//
// Print the help menu
//
static void helpFn(uint8_t argc, char *argv[]) {
	command_t *command = commands;

	if(argc < 2) {
		while(command->commandStr != NULL) {
			printf("%s - %s\n", command->commandStr, command->helpStr);
			command++;
		}
	} else {
		while(command->commandStr != NULL) {
			if(strcmp(command->commandStr, argv[1]) == 0) {
				printf("%s - %s\n", command->commandStr, command->helpStr);
				break;
			}
			command++;
		}
	}
}

// static void galvoFn(uint8_t argc, char *argv[]) {
// 	if(argc == 3) {
// 		int8_t galvo = strtoul(argv[1], NULL, 10);
// 		int32_t pos = strtol(argv[2], NULL, 10);

// 		galvoSet(galvo, pos);
		
// 	} else {
// 		printf("Invalid galvo arguments\n");
// 	}
// }


//
// Put any initialization code here
//
void consoleInit() {

	galvoInit();

	// Init Laser
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOE, ENABLE);
	GPIO_Init(GPIOE, &(GPIO_InitTypeDef){GPIO_Pin_4, GPIO_Mode_OUT, GPIO_Speed_2MHz, GPIO_OType_PP, GPIO_PuPd_NOPULL});
	GPIO_SetBits(GPIOE, GPIO_Pin_4);
}

//
// Check to see if there is new data and process it if there is
//
void consoleProcess() {
	uint32_t inBytes = fifoSize(&usbRxFifo);

	if(inBytes > 0) {
		uint32_t newLine = 0;
		for(int32_t index = 0; index < inBytes; index++){
			if((fifoPeek(&usbRxFifo, index) == '\n') || (fifoPeek(&usbRxFifo, index) == '\r')) {
				newLine = index + 1;
				break;
			}
		}

		if(newLine > sizeof(cmdBuff)) {
			newLine = sizeof(cmdBuff) - 1;
		}

		if(newLine) {
			uint8_t *pBuf = (uint8_t *)cmdBuff;
			while(newLine--){
				*pBuf++ = fifoPop(&usbRxFifo);
			}

			// If it's an \r\n combination, discard the second one
			if((fifoPeek(&usbRxFifo, 0) == '\n') || (fifoPeek(&usbRxFifo, 0) == '\r')) {
				fifoPop(&usbRxFifo);
			}

			*(pBuf - 1) = 0; // String terminator

			argc = 0;

			// Get command
			argv[argc] = strtok(cmdBuff, " ");

			// Get arguments (if any)
			while ((argv[argc] != NULL) && (argc < sizeof(argv)/sizeof(char *))){
				argc++;
				argv[argc] = strtok(NULL, " ");
			}

			if(argc > 0) {
				command_t *command = commands;
				while(command->commandStr != NULL) {
					if(strcmp(command->commandStr, argv[0]) == 0) {
						command->fn(argc, argv);
						break;
					}
					command++;
				}

				if(command->commandStr == NULL) {
					printf("Unknown command '%s'\n", argv[0]);
					helpFn(1, NULL);
				}
			}
		}
	}
}
