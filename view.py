# Shared by master and slave: paddle buttons and drawing.
#
# Game coordinates (used by master.py and in radio messages):
#   x = axis between the players: x=0 is the master's end, x=4 the slave's
#   y = sideways position of the ball and the paddles
#
# On the screen every player has their own paddle at the bottom and the
# opponent's at the top; the ball flies up and down between them. The
# slave's view is only flipped top to bottom, so sideways positions are the
# same on both screens: a paddle on the left is on the left for both
# players. Button A moves your paddle left, B right.
# Your own paddle is also brighter than the opponent's.

from microbit import display, button_a, button_b, sleep, Image
from micropython import const
import machine

_PAD = const(2)          # paddle length in pixels (keep in sync with master/slave)
_WIN_SCORE = const(5)    # points needed to win (keep in sync with master.py)
_MISS_SHOW = const(700)     # how long the missed ball stays visible before the score
_SCORE_DELAY = const(600)   # how long each character of the score ("2-1") is shown

_BRIGHT_ME = const(9)
_BRIGHT_OTHER = const(4)
_BRIGHT_BALL = const(9)

_PLAY = const(0)
_POINT = const(1)

img = Image(5, 5)
shown_phase = _PLAY   # last phase we displayed
phase_changed = 0     # when it changed (ms)
msg_shown = False     # score / result already shown for this phase


# Move my paddle (index me in pad) by the buttons: A left, B right.
# Returns True if it moved.
def buttons(pad, me):
    moved = False
    if button_a.was_pressed() and pad[me] > 0:
        pad[me] -= 1
        moved = True
    if button_b.was_pressed() and pad[me] < 5 - _PAD:
        pad[me] += 1
        moved = True
    return moved


# Draw the field, or the score / result after a point. me is the index of
# my paddle (0 = master, 1 = slave); my paddle is always drawn at the bottom.
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
            img.set_pixel(pad[me] + i, 4, _BRIGHT_ME)          # me: bottom
            img.set_pixel(pad[1 - me] + i, 0, _BRIGHT_OTHER)   # opponent: top
        # my end of the game x axis is the bottom row (the slave flips it)
        img.set_pixel(by, 4 - bx if me == 0 else bx, _BRIGHT_BALL)
        display.show(img)
    elif not msg_shown:
        msg_shown = True
        if phase == _POINT:
            # my score first
            display.show("%d-%d" % (score[me], score[1 - me]),
                         delay=_SCORE_DELAY, wait=False)
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
