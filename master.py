# Master: runs the ball and the score, broadcasts the state.
# Its paddle is index 0 (left in game coordinates); the slave's comes by radio.

from microbit import sleep, running_time
from micropython import const
import radio
import random
import machine
from net import recv
import view

_PAD = const(2)             # paddle length in pixels (keep in sync with view.py)
_WIN_SCORE = const(5)       # points needed to win (keep in sync with view.py)
_TICK = const(80)           # how often (ms) the state is sent
_LINK_TIMEOUT = const(3000) # no message from the slave for this long -> reset
_BALL_START = const(450)    # ms per ball step at the start of a rally
_BALL_MIN = const(150)      # fastest ball
_BALL_SPEEDUP = const(25)   # speedup after each paddle hit
_PAUSE = const(2000)        # pause after a point (score display)
_OVER_PAUSE = const(3000)   # how long the result is shown before reset

_PLAY = const(0)
_POINT = const(1)
_OVER = const(2)


# Bounce off the top/bottom wall. Returns (new_y, new_dy).
def bounce_y(by, dy):
    ny = by + dy
    if ny < 0 or ny > 4:
        dy = -dy
        ny = by + dy
    return ny, dy


def run(my_id):
    pad = [(5 - _PAD) // 2] * 2       # top pixel of each paddle [left, right]
    score = [0, 0]
    bx, by = 2, 2
    dx, dy = random.choice((-1, 1)), random.choice((-1, 0, 1))
    ball_ms = _BALL_START
    phase = _PLAY

    now = running_time()
    next_ball = now + 1000            # short delay before the first serve
    next_send = 0
    phase_end = 0                     # when POINT/OVER ends
    last_heard = now

    while True:
        now = running_time()

        if view.buttons(pad, 0):
            next_send = 0             # send right away

        # --- receive the slave's paddle ------------------------------------
        while True:
            p = recv()
            if p is None:
                break
            if p[0] == "P" and len(p) == 2:
                try:
                    pad[1] = min(max(int(p[1]), 0), 5 - _PAD)
                    last_heard = now
                except ValueError:
                    pass              # malformed message, ignore

        if now - last_heard > _LINK_TIMEOUT:
            view.lost()

        # --- ball and score ------------------------------------------------
        if phase == _PLAY and now >= next_ball:
            next_ball = now + ball_ms
            ny, dy = bounce_y(by, dy)
            nx = bx + dx
            if nx == 0 or nx == 4:
                side = 0 if nx == 0 else 1
                if pad[side] <= ny < pad[side] + _PAD:
                    # paddle hit: reverse, random angle, speed up
                    dx = -dx
                    dy = random.choice((-1, 0, 1))
                    ball_ms = max(_BALL_MIN, ball_ms - _BALL_SPEEDUP)
                    nx = bx + dx
                    ny, dy = bounce_y(by, dy)
                else:
                    # missed -> point for the opponent
                    winner = 1 - side
                    score[winner] += 1
                    if score[winner] >= _WIN_SCORE:
                        phase = _OVER
                        phase_end = now + _OVER_PAUSE
                    else:
                        phase = _POINT
                        phase_end = now + _PAUSE
            bx, by = nx, ny
        elif phase != _PLAY and now >= phase_end:
            if phase == _OVER:
                machine.reset()
            phase = _PLAY
            bx, by = 2, 2
            dx, dy = random.choice((-1, 1)), random.choice((-1, 0, 1))
            ball_ms = _BALL_START
            next_ball = now + 600

        # --- send the state ------------------------------------------------
        if now >= next_send:
            next_send = now + _TICK
            radio.send("S:%d:%d:%d:%d:%d:%d" % (
                bx, by, pad[0], score[0], score[1], phase))

        view.render(now, phase, pad, 0, bx, by, score)
        sleep(10)
