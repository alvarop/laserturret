PROJNAME = turretVision

SRC = turretVision.cpp

CLFAGS := $(shell pkg-config opencv --cflags)
LIBS := $(shell pkg-config opencv --libs)

CC = g++

all:
	$(CC) $(CFLAGS) $(SRC) -o $(PROJNAME) $(LIBS)
