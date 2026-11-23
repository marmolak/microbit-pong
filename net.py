# Radio setup, message receiving and the handshake (who is the master).
#
# Protocol: raw bytes, the first byte is the message type (an ASCII letter,
# so a message printed in the REPL is still partly readable):
#   H <id_hi> <id_lo>                   3 B  handshake, until roles are known
#   S <bx> <by> <p0> <s0> <s1> <phase>  7 B  state from master (ball, left
#                                            paddle, score, game phase)
#   P <p1>                              2 B  right paddle from slave
#
# Bytes instead of text: values are small numbers, so each fits in one
# byte. Messages are received into one preallocated buffer and sent from
# preallocated buffers, so the main loop creates no objects on the heap
# (no strings, no split(), no int()) and the garbage collector stays idle.

from microbit import display, sleep, running_time, Image
from micropython import const
import radio
import random
import machine

_GROUP = const(17)  # radio group; another pair nearby should use a different one

_MSG_HELLO = const(0x48)  # 'H'
_MSG_STATE = const(0x53)  # 'S'

# Seed the RNG from the chip's unique serial number, so the two devices
# never generate the same sequence of IDs (that would loop the handshake
# forever). Kept below 2**30 to stay a MicroPython small int.
seed = running_time()
for b in machine.unique_id():
    seed = (seed * 31 + b) & 0x3FFFFFFF
random.seed(seed)

radio.config(group=_GROUP, length=32, queue=6)
radio.on()

buf = bytearray(8)    # every received message lands here (reused)
hello = bytearray(3)  # outgoing H message (reused)


# Receive the next message into buf. Returns its length, or None if the
# queue is empty. This is the only place that reads the radio, so no
# message gets lost by being read by someone else. A message longer than
# buf is cut, but its full length is returned, so length checks reject it.
def recv():
    return radio.receive_bytes_into(buf)


def send_hello(my_id):
    hello[0] = _MSG_HELLO
    hello[1] = my_id >> 8
    hello[2] = my_id & 0xFF
    radio.send_bytes(hello)


# Agree on roles. Returns (is_master, my_id).
def handshake():
    my_id = random.randint(1, 30000)  # fits in 2 bytes
    next_send = 0
    frame = 0
    while True:
        now = running_time()
        if now >= next_send:
            send_hello(my_id)
            # random gap so both devices don't keep transmitting at once
            next_send = now + 150 + random.randint(0, 100)
            display.show(Image.ALL_CLOCKS[frame % 12])
            frame += 1

        while True:
            n = recv()
            if not n:
                break
            if n == 3 and buf[0] == _MSG_HELLO:
                other = (buf[1] << 8) | buf[2]
                if other == my_id:
                    my_id = random.randint(1, 30000)  # collision, try again
                    continue
                # send our ID once more so the other side surely has it
                send_hello(my_id)
                return my_id > other, my_id
            if n == 7 and buf[0] == _MSG_STATE:
                # master is already playing -> it saw our ID and its is higher
                return False, my_id
        sleep(20)
