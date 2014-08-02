#ifndef __QDECODER_H__
#define __QDECODER_H__

#include <stdint.h>

void qdecoderInit();
void qdecoderReset(uint8_t ch);
int16_t qdecoderGet(uint8_t ch);
void qdecoderProcess();

#endif
