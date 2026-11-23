# Shared by master and slave: paddle buttons and drawing.
#
# The game runs in one shared coordinate system: the master's paddle is on
# the left (x=0), the slave's on the right (x=4). When drawing, the slave
# mirrors the field, so every player sees their own paddle on the left.
# Your own paddle is also brighter than the opponent's.

from microbit import display, button_a, button_b, sleep, Image
from micropython import const
import machine

_PAD = const(2)          # paddle length in pixels (keep in sync with master/slave)
_WIN_SCORE = const(5)    # points needed to win (keep in sync with master.py)
_MISS_SHOW = const(500)  # how long the missed ball stays visible before the score

_BRIGHT_ME = const(9)
_BRIGHT_OTHER = const(4)
_BRIGHT_BALL = const(9)

_PLAY = const(0)
_POINT = const(1)

img = Image(5, 5)
shown_phase = _PLAY   # last phase we displayed
phase_changed = 0     # when it changed (ms)
msg_shown = False     # score / result already shown for this phase


# Move my paddle (index me in pad) by the buttons. Returns True if it moved.
def buttons(pad, me):
    moved = False
    if button_a.was_pressed() and pad[me] < 5 - _PAD:
        pad[me] += 1
        moved = True
    if button_b.was_pressed() and pad[me] > 0:
        pad[me] -= 1
        moved = True
    return moved


# Draw the field, or the score / result after a point. me is the index of
# my paddle (0 = master, 1 = slave); my paddle is always drawn on the left.
# Returns how many ms ago the phase changed.
def render(now, phase, pad, me, bx, by, score):
    global shown_phase, phase_changed, msg_shown
    if phase != shown_phase:
        shown_phase = phase
        phase_changed = now
        msg_shown = False

    if phase == _PLAY or now - phase_changed < _MISS_SHOW:
        img.fill(0)
        for i in range(_PAD):
            img.set_pixel(0, pad[me] + i, _BRIGHT_ME)          # me: left
            img.set_pixel(4, pad[1 - me] + i, _BRIGHT_OTHER)   # opponent: right
        # the slave mirrors the ball's x (master's x=0 is the slave's x=4)
        img.set_pixel(bx if me == 0 else 4 - bx, by, _BRIGHT_BALL)
        display.show(img)
    elif not msg_shown:
        msg_shown = True
        if phase == _POINT:
            # my score first, matching my paddle on the left
            display.show("%d-%d" % (score[me], score[1 - me]),
                         delay=350, wait=False)
        elif score[me] >= _WIN_SCORE:
            display.show(Image.HAPPY)
        else:
            display.show(Image.SAD)
    return now - phase_changed


# The other device went silent: show a cross and start over.
def lost():
    display.show(Image.NO)
    sleep(1000)
    machine.reset()
