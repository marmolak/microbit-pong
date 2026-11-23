# Radio setup, message receiving and the handshake (who is the master).
#
# Protocol (text messages, fields separated by ':'):
#   H:<id>                         handshake, sent until roles are known
#   S:<bx>:<by>:<p0>:<s0>:<s1>:<f> state from master (ball, left paddle,
#                                  score, game phase)
#   P:<p1>                         right paddle position from slave

from microbit import display, sleep, running_time, Image
from micropython import const
import radio
import random
import machine

_GROUP = const(17)  # radio group; another pair nearby should use a different one

# Seed the RNG from the chip's unique serial number, so the two devices
# never generate the same sequence of IDs (that would loop the handshake
# forever). Kept below 2**30 to stay a MicroPython small int.
seed = running_time()
for b in machine.unique_id():
    seed = (seed * 31 + b) & 0x3FFFFFFF
random.seed(seed)

radio.config(group=_GROUP, length=32, queue=6)
radio.on()


# Return the next received message split into fields, or None if the queue
# is empty. This is the only place that reads the radio, so no message gets
# lost by being read by someone else.
def recv():
    while True:
        try:
            m = radio.receive()
        except ValueError:
            continue  # corrupted packet
        if m is None:
            return None
        return m.split(":")


# Agree on roles. Returns (is_master, my_id).
def handshake():
    my_id = random.randint(1, 30000)
    next_send = 0
    frame = 0
    while True:
        now = running_time()
        if now >= next_send:
            radio.send("H:%d" % my_id)
            # random gap so both devices don't keep transmitting at once
            next_send = now + 150 + random.randint(0, 100)
            display.show(Image.ALL_CLOCKS[frame % 12])
            frame += 1

        while True:
            p = recv()
            if p is None:
                break
            if p[0] == "H" and len(p) == 2:
                try:
                    other = int(p[1])
                except ValueError:
                    continue
                if other == my_id:
                    my_id = random.randint(1, 30000)  # collision, try again
                    continue
                # send our ID once more so the other side surely has it
                radio.send("H:%d" % my_id)
                return my_id > other, my_id
            if p[0] == "S":
                # master is already playing -> it saw our ID and its is higher
                return False, my_id
        sleep(20)
