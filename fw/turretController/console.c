#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "console.h"
#include "fifo.h"
#include "servo.h"
#include "stepper.h"
#include "qik.h"

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
static void servoCmd(uint8_t argc, char *argv[]);
static void laserCmd(uint8_t argc, char *argv[]);
static void stepperCmd(uint8_t argc, char *argv[]);
static void qikCmd(uint8_t argc, char *argv[]);

static command_t commands[] = {
	{"stepper", stepperCmd, "Usage: \n"
							"\tstepper <stepperId> <on|off>\n"
							"\tstepper <stepperId> pos\n"
							"\tstepper <stepperId> pos <new position> <speed>\n"
							"\tstepper <stepperId> bounds <lower bound> <upper bound>\n"
							"\tstepper <stepperId> mov <direction> <speed> <count>\n"},
	{"servo", servoCmd, "Usage: servo <servoId> <position (1000-2000)>"},
	{"laser", laserCmd, "Usage: laser <0, 1>"},
	{"qik"	, qikCmd,	"Usage: qik"},
	// Add new commands here!
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

static void servoCmd(uint8_t argc, char *argv[]) {
	if(argc > 2) {
		uint8_t servo = (uint8_t)strtoul(argv[1], NULL, 10);
		uint16_t position = (uint16_t)strtoul(argv[2], NULL, 10);
		servoSetPosition(servo, position);
	} else {
		printf("Invalid arguments\n");
		
		argv[1] = argv[0];
		helpFn(2, argv);
	}
}

static void laserCmd(uint8_t argc, char *argv[]) {
	if(argc > 1) {
		uint8_t state = (uint8_t)strtoul(argv[1], NULL, 10);
		if(state) {
			GPIO_ResetBits(GPIOE, GPIO_Pin_4);		
		} else {
			GPIO_SetBits(GPIOE, GPIO_Pin_4);
		}
	} else {
		printf("Invalid arguments\n");
		
		argv[1] = argv[0];
		helpFn(2, argv);
	}
}

static void stepperCmd(uint8_t argc, char *argv[]) {
	switch(argc) {
		case 3: {
			uint8_t stepper = (uint8_t)strtoul(argv[1], NULL, 10);

			if(strcmp("pos", argv[2]) == 0) {
				printf("Stepper %d position %d\n", stepper, stepperGetPosition(stepper));
			} else if(strcmp("bounds", argv[2]) == 0) {
				int16_t lBound;
				int16_t uBound;

				stepperGetBounds(stepper, &lBound, &uBound);
				
				printf("Stepper %d bounds (%d, %d)\n", stepper, lBound, uBound);
			} else if(strcmp("on", argv[2]) == 0) {
				stepperEnable(stepper);
			} else if(strcmp("off", argv[2]) == 0) {
				stepperDisable(stepper);
			}
			break;
		}

		case 5: {
			uint8_t stepper = (uint8_t)strtoul(argv[1], NULL, 10);

			if(strcmp("pos", argv[2]) == 0) {
				int16_t newPos = strtol(argv[3], NULL, 10);
				uint16_t speed = (uint16_t)strtoul(argv[4], NULL, 10);
				
				//printf("Set Stepper %d position to %d at speed %d\n", stepper, newPos, speed);
				
				stepperSetPosition(stepper, newPos, speed);
			} else if(strcmp("bounds", argv[2]) == 0) {
				int16_t lBound = strtol(argv[3], NULL, 10);
				int16_t uBound = strtol(argv[4], NULL, 10);

				stepperSetBounds(stepper, lBound, uBound);
				
				printf("Set Stepper %d bounds to (%d, %d)\n", stepper, lBound, uBound);
			}

			break;
		}

		case 6: {
			uint8_t stepper = (uint8_t)strtoul(argv[1], NULL, 10);

			if(strcmp("mov", argv[2]) == 0) {
				uint16_t direction = (uint16_t)strtoul(argv[3], NULL, 10);
				uint16_t speed = (uint16_t)strtoul(argv[4], NULL, 10);
				uint16_t count = (uint16_t)strtoul(argv[5], NULL, 10);
				
				//printf("Stepper move %d at speed %d in dir %d\n", count, speed, direction);

				stepperSetDirection(stepper, direction);
				stepperSetSpeed(stepper, speed);
				stepperMove(stepper, count);
			}
			break;
		}

		default: {
			printf("Invalid arguments\n");
			
			argv[1] = argv[0];
			helpFn(2, argv);
			break;
		}
	}
}

static void qikCmd(uint8_t argc, char *argv[]) {
	switch(argc) {
		case 3: {
			uint8_t mot = (uint8_t)strtoul(argv[1], NULL, 10);
			if(strcmp("coast", argv[2]) == 0) {
				qikSetCoast(mot);
				//printf("M%d coast\n", mot);
			}

			break;
		}

		case 4: {
			uint8_t mot = (uint8_t)strtoul(argv[1], NULL, 10);
			int32_t speed = strtol(argv[3], NULL, 10);
			uint8_t dir = 0;
			
			if(speed > 0) {
				dir = 1;
			}

			if(strcmp("mov", argv[2]) == 0) {
				//printf("Move M%d %s at speed %d\n", mot, (dir)? "Fwd" : "Rev", abs(speed));
				qikSetSpeed(mot, abs(speed), dir);
			}

			break;
		}
	}

}

//
// Put any initialization code here
//
void consoleInit() {
	servoInit();
	stepperInit();
	qikInit();

	// Init Laser
	GPIO_Init(GPIOE, &(GPIO_InitTypeDef){GPIO_Pin_4, GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});
	GPIO_SetBits(GPIOE, GPIO_Pin_4);
}

//
// Check to see if there is new data and process it if there is
//
void consoleProcess() {
	uint32_t inBytes = fifoSize(&usbRxFifo);

	qikProcess();

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