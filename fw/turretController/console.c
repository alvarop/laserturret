#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "console.h"
#include "fifo.h"
#include "qik.h"
#include "motor.h"

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
static void laserCmd(uint8_t argc, char *argv[]);
static void qikCmd(uint8_t argc, char *argv[]);
static void motorCmd(uint8_t argc, char *argv[]);

static command_t commands[] = {
	{"laser", laserCmd, "Usage: laser <0, 1>"},
	{"qik"	, qikCmd,	"Usage: qik"},
	{"m", motorCmd,	"Usage: m <motor(0-1)> <stop | position>"},
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
				// printf("Move M%d %s at speed %d\n", mot, (dir)? "Fwd" : "Rev", abs(speed));
				qikSetSpeed(mot, abs(speed), dir);
			}

			break;
		}
	}

}

static void motorCmd(uint8_t argc, char *argv[]) {
	switch(argc) {
		case 2: {
			if(strcmp("stop", argv[1]) == 0) {
				motorStop(0);
				motorStop(1);
			} else if(strcmp("dis", argv[1]) == 0) {
				motorDisable();
			} else if(strcmp("en", argv[1]) == 0) {
				motorEnable();
			} else {
				uint8_t mot = (uint8_t)strtoul(argv[1], NULL, 10);
				if(mot < TOTAL_MOTORS) {
					printf("m %d %d\n", mot, motorGetPos(mot));
				}
			}

			break;
		}

		case 3: {
			uint8_t mot = (uint8_t)strtoul(argv[1], NULL, 10);
			int16_t pos = strtol(argv[2], NULL, 10);
			motorSetPos(mot, pos);

			break;
		}

		case 5: {
			uint8_t mot = (uint8_t)strtoul(argv[1], NULL, 10);
				
			if(strcmp("set", argv[2]) == 0)  {
				int32_t val = strtol(argv[4], NULL, 10);
				pidVar_t pidVar;

				switch(argv[3][0]) {
					case 'p': {
						pidVar = pidP;
						break;
					}

					case 'i': {
						pidVar = pidI;
						break;
					}

					case 'd': {
						pidVar = pidD;
						break;
					}

					default: {
						pidVar = pidNone;
					}
				}

				if(pidVar != pidNone) {
					motorSetPIDVar(mot, pidVar, val);
				}
			}

				

			break;
		}
	}
}

//
// Put any initialization code here
//
void consoleInit() {
	motorInit();

	// Init Laser
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOE, ENABLE);
	GPIO_Init(GPIOE, &(GPIO_InitTypeDef){GPIO_Pin_4, GPIO_Mode_OUT, GPIO_OType_PP, GPIO_Speed_2MHz, GPIO_PuPd_NOPULL});
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
