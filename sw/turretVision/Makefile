PROJNAME = turretVision

SRC = turretVision.cpp

CLFAGS := $(shell pkg-config opencv --cflags)
LIBS := $(shell pkg-config opencv --libs)
INCLUDES := -I/opt/local/include

CC = g++

all:
	$(CC) $(CFLAGS) $(SRC) -o $(PROJNAME) $(INCLUDES) $(LIBS)
