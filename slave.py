# Slave: sends its paddle, draws the state received from the master.
# Its paddle is index 1 (right in game coordinates, drawn mirrored on the left).

from microbit import sleep, running_time
from micropython import const
import radio
import machine
from net import recv
import view

_PAD = const(2)             # paddle length in pixels (keep in sync with view.py)
_TICK = const(80)           # how often (ms) the paddle is sent
_LINK_TIMEOUT = const(3000) # no message from the master for this long -> reset
_OVER_PAUSE = const(3000)   # how long the result is shown before reset

_PLAY = const(0)
_OVER = const(2)


def run(my_id):
    pad = [(5 - _PAD) // 2] * 2       # top pixel of each paddle [left, right]
    score = [0, 0]
    bx, by = 2, 2
    phase = _PLAY

    now = running_time()
    next_send = 0
    last_heard = now

    while True:
        now = running_time()

        if view.buttons(pad, 1):
            next_send = 0             # send right away

        # --- receive the state ---------------------------------------------
        while True:
            p = recv()
            if p is None:
                break
            try:
                if p[0] == "S" and len(p) == 7:
                    bx = int(p[1])
                    by = int(p[2])
                    pad[0] = int(p[3])
                    score[0] = int(p[4])
                    score[1] = int(p[5])
                    phase = int(p[6])
                    last_heard = now
                elif p[0] == "H":
                    # master hasn't seen us yet (missed our H) -> reply
                    radio.send("H:%d" % my_id)
            except ValueError:
                pass                  # malformed message, ignore

        if now - last_heard > _LINK_TIMEOUT:
            view.lost()

        # --- send my paddle ------------------------------------------------
        if now >= next_send:
            next_send = now + _TICK
            radio.send("P:%d" % pad[1])

        since = view.render(now, phase, pad, 1, bx, by, score)
        if phase == _OVER and since > _OVER_PAUSE:
            machine.reset()
        sleep(10)
