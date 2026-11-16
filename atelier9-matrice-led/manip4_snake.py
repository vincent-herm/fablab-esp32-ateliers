from machine import Pin, SPI, TouchPad
from time import sleep_ms, ticks_ms, ticks_diff
from random import randint

# --- Hardware ---
spi = SPI(2, baudrate=10_000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
cs  = Pin(5, Pin.OUT)
t_left  = TouchPad(Pin(4))   # D4  → tourner à gauche
t_right = TouchPad(Pin(15))  # D15 → tourner à droite

SEUIL = 200
W, H = 8, 32

# --- MAX7219 init ---
def _cmd(reg, val):
    cs(0)
    for _ in range(4): spi.write(bytearray([reg, val]))
    cs(1)
for r, v in [(12,0),(15,0),(11,7),(9,0),(10,2),(12,1)]:
    _cmd(r, v)

buf = bytearray(H)

def show():
    for r in range(8):
        cs(0)
        for chip in range(4):
            byte = 0
            for k in range(8):
                if buf[chip * 8 + k] & (0x80 >> r):
                    byte |= (0x80 >> k)
            spi.write(bytearray([1 + r, byte]))
        cs(1)

def set_pixel(x, y, v=1):
    if 0 <= x < W and 0 <= y < H:
        if v: buf[y] |=  (0x80 >> x)
        else: buf[y] &= ~(0x80 >> x)

# 0=haut 1=droite 2=bas 3=gauche
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

def new_food(snake):
    while True:
        fx, fy = randint(0, W - 1), randint(0, H - 1)
        if (fx, fy) not in snake:
            return fx, fy

def step_ms(length):
    # 350 ms au départ → 150 ms à partir de 23 segments
    return max(150, 350 - (length - 3) * 10)

def game_over_anim():
    for _ in range(4):
        buf[:] = bytearray([0xFF] * H)
        show()
        sleep_ms(150)
        buf[:] = bytearray(H)
        show()
        sleep_ms(150)

def reset():
    s = [(4, 4), (4, 3), (4, 2)]   # tête en bas, corps au-dessus → direction bas libre
    return s, 2, new_food(s)        # serpent, direction (bas), nourriture

snake, direction, (fx, fy) = reset()
prev_l = prev_r = False
last_step = ticks_ms()

while True:
    now = ticks_ms()
    l = t_left.read()  < SEUIL
    r = t_right.read() < SEUIL

    if l and not prev_l:
        direction = (direction - 1) % 4   # virer à gauche
    elif r and not prev_r:
        direction = (direction + 1) % 4   # virer à droite

    prev_l, prev_r = l, r

    if ticks_diff(now, last_step) >= step_ms(len(snake)):
        last_step = now
        dx, dy = DIRS[direction]
        nx, ny = snake[0][0] + dx, snake[0][1] + dy

        # Mur ou corps → game over
        if nx < 0 or nx >= W or ny < 0 or ny >= H or (nx, ny) in snake[:-1]:
            show()
            sleep_ms(300)
            game_over_anim()
            snake, direction, (fx, fy) = reset()
            last_step = ticks_ms()
            continue

        # Mange la nourriture → grandit
        if nx == fx and ny == fy:
            snake = [(nx, ny)] + snake
            fx, fy = new_food(snake)
        else:
            snake = [(nx, ny)] + snake[:-1]

    # Dessin : serpent + nourriture (clignote toutes les 300 ms)
    buf[:] = bytearray(H)
    for x, y in snake:
        set_pixel(x, y)
    if ticks_ms() // 300 % 2 == 0:
        set_pixel(fx, fy)
    show()
    sleep_ms(20)
