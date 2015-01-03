#ifndef __GALVO_H__
#define __GALVO_H__

#include <stdint.h>

void galvoInit();
void galvoSet(uint8_t galvo, int32_t pos);
int32_t galvoGet(uint8_t galvo);

#endif
