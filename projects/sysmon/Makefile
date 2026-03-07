CC = gcc
CFLAGS = -Wall -Wextra -O2
SRC = src/sysmon.c
BIN = sysmon
INSTALL_DIR = ~/.local/bin

all: $(BIN)

$(BIN): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(BIN)

install: $(BIN)
	mkdir -p $(INSTALL_DIR)
	mv $(BIN) $(INSTALL_DIR)/$(BIN)

clean:
	rm -f $(BIN)