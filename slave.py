# Slave: sends its paddle, draws the state received from the master.
# Its paddle is index 1 (the x=4 end in game coordinates, see view.py).

from microbit import sleep, running_time
from micropython import const
import radio
import machine
from net import recv, buf, send_hello
import view

_MSG_HELLO = const(0x48)    # 'H', message types: see net.py
_MSG_STATE = const(0x53)    # 'S'
_MSG_PADDLE = const(0x50)   # 'P'

_PAD = const(2)             # paddle length in pixels (keep in sync with view.py)
_TICK = const(80)           # how often (ms) the paddle is sent
_LINK_TIMEOUT = const(3000) # no message from the master for this long -> reset
_OVER_PAUSE = const(3000)   # how long the result is shown before reset

_PLAY = const(0)
_OVER = const(2)


def run(my_id):
    pad = [(5 - _PAD) // 2] * 2       # lowest y of each paddle [master, slave]
    score = [0, 0]
    bx, by = 2, 2
    phase = _PLAY
    paddle = bytearray(2)             # outgoing P message (reused)
    paddle[0] = _MSG_PADDLE

    now = running_time()
    next_send = 0
    last_heard = now

    while True:
        now = running_time()

        if view.buttons(pad, 1):
            next_send = 0             # send right away

        # --- receive the state ---------------------------------------------
        while True:
            n = recv()
            if not n:
                break
            if n == 7 and buf[0] == _MSG_STATE:
                # check ranges, a bad value would crash display.set_pixel
                if buf[1] < 5 and buf[2] < 5 and buf[3] <= 5 - _PAD:
                    bx = buf[1]
                    by = buf[2]
                    pad[0] = buf[3]
                    score[0] = buf[4]
                    score[1] = buf[5]
                    phase = buf[6]
                    last_heard = now
            elif n == 3 and buf[0] == _MSG_HELLO:
                # master hasn't seen us yet (missed our H) -> reply
                send_hello(my_id)

        if now - last_heard > _LINK_TIMEOUT:
            view.lost()

        # --- send my paddle ------------------------------------------------
        if now >= next_send:
            next_send = now + _TICK
            paddle[1] = pad[1]
            radio.send_bytes(paddle)

        since = view.render(now, phase, pad, 1, bx, by, score)
        if phase == _OVER and since > _OVER_PAUSE:
            machine.reset()
        sleep(10)
