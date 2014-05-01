#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "console.h"
#include "fifo.h"
#include "target.h"

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
static void init(uint8_t argc, char *argv[]);
static void set(uint8_t argc, char *argv[]);
static void read(uint8_t argc, char *argv[]);
static void calibrate(uint8_t argc, char *argv[]);
static void hitThreshold(uint8_t argc, char *argv[]);
static void start(uint8_t argc, char *argv[]);
static void stop(uint8_t argc, char *argv[]);

static command_t commands[] = {
	{"init", init, "Usage: init - init targets (re-scan)"},
	{"set", set, "Usage: set <target> <0,1>"},
	{"read", read, "Usage: read <target>"},
	{"cal", calibrate, "Usage: cal <target> <0(miss),1(hit)>"},
	{"ht", hitThreshold, "Usage: ht <target> [new threshold]"},
	{"start", start, "Usage: start"},
	{"stop", stop, "Usage: stop"},
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

//
// Init
//
static void init(uint8_t argc, char *argv[]) {
	targetInit();	
}

//
// Set target enabled/disabled
//
static void set(uint8_t argc, char *argv[]) {
	if(argc > 1) {
		uint8_t target = strtoul(argv[1], NULL, 10);
		uint8_t enable = strtoul(argv[2], NULL, 10);
		targetSet(target, enable);
	}
}

//
// read target adc value
//
static void read(uint8_t argc, char *argv[]) {
	if(argc > 1) {
		uint8_t target = strtoul(argv[1], NULL, 10);
		printf("Target %d = %d\n", target, targetRead(target));
	}
}

//
// Calibrate high/low value for target
//
static void calibrate(uint8_t argc, char *argv[]) {
	if(argc > 2) {
		uint8_t target = strtoul(argv[1], NULL, 10);
		uint8_t state = strtoul(argv[2], NULL, 10);
		targetCalibrate(target, state);
	}
}

//
// Set/get hit threshold
//
static void hitThreshold(uint8_t argc, char *argv[]) {
	if(argc == 2) {
		uint8_t target = strtoul(argv[1], NULL, 10);
		printf("%d ht %d\n", target, targetGetHitThreshold(target));
	} else if(argc == 3) {
		uint8_t target = strtoul(argv[1], NULL, 10);
		uint16_t newThreshold = strtoul(argv[2], NULL, 10);

		targetSetHitThreshold(target, newThreshold);
	}
}

static void start(uint8_t argc, char *argv[]) {
	printf("Starting targets\n");
	uint8_t all = 0;
	
	if((argc > 1) && strcmp("all", argv[1]) == 0) {
		all = 1;
	}

	targetStart(all);
}

static void stop(uint8_t argc, char *argv[]) {
	printf("Stopping targets\n");
	targetStop();
}

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
