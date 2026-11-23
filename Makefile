# Flash the game to a micro:bit v1.
#
#   make install   flash MicroPython, then copy all game files
#   make runtime   flash only the MicroPython runtime (wipes the filesystem)
#   make put       copy the game files (MicroPython must already be flashed)
#   make ls        list files on the micro:bit
#
# Needs uflash and ufs (pip install uflash microfs). Run once per micro:bit;
# both get exactly the same files.

UFLASH ?= uflash
UFS ?= ufs
# max seconds to wait for the micro:bit after flashing
WAIT ?= 30

# main.py goes last, so nothing starts before all modules are in place
MODULES := net.py view.py master.py slave.py
MAIN := main.py

.PHONY: install runtime wait put ls

install: runtime wait put
	@echo "Done. Press reset on the back of the micro:bit."

runtime:
	$(UFLASH)

# After uflash the micro:bit programs itself and reboots; wait until its
# REPL answers, otherwise ufs fails with "Could not enter raw REPL".
wait:
	@echo "Waiting for the micro:bit..."
	@for i in $$(seq $(WAIT)); do \
		$(UFS) ls >/dev/null 2>&1 && exit 0; \
		sleep 1; \
	done; \
	echo "micro:bit did not answer within $(WAIT) s" >&2; exit 1

put:
	@for f in $(MODULES) $(MAIN); do \
		echo "ufs put $$f"; \
		$(UFS) put $$f || exit 1; \
	done

ls:
	$(UFS) ls
