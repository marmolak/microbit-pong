from microbit import *
from radio import *
import radio
import random
import machine

class PlayerData:
    pos_y = enemy_pos_y = 2
    prev_pos_y = enemy_prev_pos_y = pos_y
    role  = None
    bright = 9

class Direction:
    STREIGHT = 0
    DOWN = 1
    UP = 2
    STREIGHT_BACK = 3
    DOWN_BACK = 4
    UP_BACK = 5
    DIRECTIONS = [ 0, 1, 2, 3, 4, 5 ]
    BALL_DIRECTIONS = [
        (1, 0),    # st direct
        (-1, 0),   # st back
        (1, -1),   # up direct
        (-1, -1),  # up back
        (1, 1),    # down direct
        (-1, 1),   # down back
    ]

class Ball:
    pos_x = pos_y = 2
    prev_pos_x = prev_pos_y = pos_x
    direction = random.choice(Direction.DIRECTIONS)
    bright = 7
    move_time = None
    timeout = 500

def initial_handshake():
    other_id = None
    handshake_done = False
    display.scroll("W")
    my_id = random.randint(0, 1000)

    for _ in range(5):
        radio.send(str(my_id))
        sleep(200)

    start_time = running_time()
    timeout = 5000  # 5 seconds

    while running_time() - start_time < timeout:
        msg = radio.receive()
        if msg:
            try:
                other_id = int(msg)
                break
            except:
                pass
        sleep(100)

    # Are we received something like int?
    if other_id is None:
        return False

    if my_id > other_id:
        PlayerData.role = "mmm"
    elif my_id < other_id:
        PlayerData.role = "bbb"
    else:
        PlayerData.role = "retry"

    if PlayerData.role != "retry":
        handshake_done = True

    if handshake_done:
        #display.scroll(PlayerData.role.upper())
        pass
    else:
        display.show(Image.CONFUSED)
    return handshake_done

def game_sync():
    max_wait = 50

    if PlayerData.role == "mmm":
        radio.send("MPING")

        for _ in range(max_wait):
            mpong = radio.receive()
            if mpong and mpong == "MPONG":
                return True
            sleep(100)
    else:
        for _ in range(max_wait):
            mping = radio.receive()
            if mping and mping == "MPING":
                radio.send("MPONG")
                return True
            sleep(100)
    return False

def reverse_direction():
    if Ball.direction == Direction.STREIGHT:
        Ball.direction = Direction.STREIGHT_BACK
    elif Ball.direction == Direction.DOWN:
        Ball.direction = Direction.DOWN_BACK
    elif Ball.direction == Direction.UP:
        Ball.direction = Direction.UP_BACK
    elif Ball.direction == Direction.STREIGHT_BACK:
        Ball.direction = Direction.STREIGHT
    elif Ball.direction == Direction.DOWN_BACK:
        Ball.direction = Direction.DOWN
    elif Ball.direction == Direction.UP_BACK:
        Ball.direction = Direction.UP

def ball():
    if not Ball.move_time:
        Ball.move_time = running_time()

    if running_time() - Ball.move_time >= Ball.timeout:
        Ball.prev_pos_x = Ball.pos_x
        Ball.prev_pos_y = Ball.pos_y
        Ball.move_time = running_time()

        if PlayerData.role == "mmm":
            dx, dy = Direction.BALL_DIRECTIONS[Ball.direction]
            Ball.pos_x = max(0, min(4, Ball.pos_x + dx))
            Ball.pos_y = max(0, min(4, Ball.pos_y + dy))
            radio.send("b:" + str(Ball.pos_x) + ":" + str(Ball.pos_y) + ":" + str(Ball.direction)   )
        else:
            ball_packet = str(radio.receive())
            if ball_packet and ball_packet.startswith("b:"):
                _, pos_x, pos_y, direction = ball_packet.split(':')
                Ball.pos_x = int(pos_x)
                Ball.pos_y = int(pos_y)
                Ball.direction = int(direction)
                reverse_direction()

    if Ball.pos_x != Ball.prev_pos_x or Ball.pos_y != Ball.prev_pos_y:
        display.set_pixel(Ball.prev_pos_x, Ball.prev_pos_y, 0);
    display.set_pixel(Ball.pos_x, Ball.pos_y, Ball.bright);

    if (Ball.pos_x == 4 or Ball.pos_x == 0) and PlayerData.pos_y != Ball.pos_y:
        sleep(1000)
        display.scroll(">>> GAME OVER <<<")
        sleep(1000)
        machine.reset()

def game_loop():

    ball()

    PlayerData.prev_pos_y = PlayerData.pos_y

    if button_a.was_pressed() and PlayerData.pos_y != 4:
        PlayerData.pos_y = PlayerData.pos_y + 1

    if button_b.was_pressed() and PlayerData.pos_y != 0:
        PlayerData.pos_y = PlayerData.pos_y - 1

    radio.send("y:" + str(PlayerData.pos_y))

    PlayerData.enemy_prev_pos_y = PlayerData.enemy_pos_y
    enemy_pos_y_packet = str(radio.receive())
    if enemy_pos_y_packet and enemy_pos_y_packet.startswith("y:"):
        _, enemy_pos_y_tmp = enemy_pos_y_packet.split(":")
        PlayerData.enemy_pos_y = int(enemy_pos_y_tmp)

    if PlayerData.prev_pos_y is not PlayerData.pos_y:
        display.set_pixel(0, PlayerData.prev_pos_y, 0)
    display.set_pixel(0, PlayerData.pos_y, PlayerData.bright)

    if PlayerData.enemy_prev_pos_y is not PlayerData.enemy_pos_y:
        display.set_pixel(4, PlayerData.enemy_prev_pos_y, 0)
    display.set_pixel(4, PlayerData.enemy_pos_y, PlayerData.bright)

radio.on()

while True:
    if initial_handshake():
        break
    sleep(1000)

if not game_sync():
    machine.reset()

while True:
    game_loop()