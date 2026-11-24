# Pong for 2 players on two micro:bits connected by radio.
#
# Both devices run the same firmware. After power-on they agree on who is
# the master (higher random ID, see net.py). The master runs the game
# (master.py), the slave only sends its paddle (slave.py); drawing and
# buttons are shared (view.py).
#
# The code is split into modules because micro:bit v1 has only 16 KB RAM:
# MicroPython compiles each module separately and frees the parse tree in
# between. Each device compiles only the code for its own role, and only
# after the handshake code has been freed.
#
# Flashing: `make install` (see Makefile), then press reset.
# It runs uflash (MicroPython only, wipes the filesystem), waits for the
# micro:bit to reboot and copies all modules with ufs, main.py last.

import gc
from microbit import display, sleep, Image
import net

is_master, my_id = net.handshake()
# every player's own paddle is at the bottom: look down
display.show(Image.ARROW_S)

net.handshake = None    # not needed any more, let gc free its bytecode
gc.collect()
if is_master:
    import master as game
else:
    import slave as game
gc.collect()

sleep(1000)
game.run(my_id)
