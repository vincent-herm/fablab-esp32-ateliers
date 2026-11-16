from machine import Pin, SPI, TouchPad
from time import sleep_ms, ticks_ms, ticks_diff
from random import randint, choice

# --- Hardware ---
spi = SPI(2, baudrate=10_000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
cs  = Pin(5, Pin.OUT)
t_left  = TouchPad(Pin(4))   # D4  → raquette à gauche
t_right = TouchPad(Pin(15))  # D15 → raquette à droite

SEUIL = 200
W, H = 8, 32   # 8 colonnes × 32 lignes

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

def draw(bx, by, px):
    buf[:] = bytearray(H)
    for i in range(3):
        set_pixel(px + i, H - 1, 1)  # raquette (3 pixels, rangée du bas)
    set_pixel(bx, by, 1)             # balle
    show()

def game_over_anim():
    for _ in range(4):
        buf[:] = bytearray([0xFF] * H)
        show()
        sleep_ms(150)
        buf[:] = bytearray(H)
        show()
        sleep_ms(150)

def speed_ms(bounces):
    # 4 LED/s au départ (250 ms), 20 LED/s après 10 rebonds (50 ms)
    spd = 4 + (16 * min(bounces, 10)) // 10
    return 1000 // spd

def reset():
    return (randint(1, W - 2), 2,   # bx, by
            choice([-1, 1]), 1,      # dx, dy
            W // 2 - 1, 0)           # px (raquette), bounces

bx, by, dx, dy, px, bounces = reset()
prev_l = prev_r = False
last_move = ticks_ms()
last_pad  = ticks_ms()

while True:
    now = ticks_ms()
    l = t_left.read()  < SEUIL
    r = t_right.read() < SEUIL

    # Raquette : nouvelle presse ou maintien (répétition 150 ms)
    if l and (not prev_l or ticks_diff(now, last_pad) >= 150):
        if px > 0:        px -= 1; last_pad = now
    elif r and (not prev_r or ticks_diff(now, last_pad) >= 150):
        if px < W - 3:    px += 1; last_pad = now

    prev_l, prev_r = l, r

    # Déplacement de la balle
    if ticks_diff(now, last_move) >= speed_ms(bounces):
        last_move = now
        nx, ny = bx + dx, by + dy

        # Rebonds sur les murs gauche/droite
        if nx < 0:   nx = 0;      dx = 1
        if nx >= W:  nx = W - 1;  dx = -1
        # Rebond sur le plafond
        if ny < 0:   ny = 0;      dy = 1

        # Bas : raquette ou game over
        if ny >= H - 1:
            ny = H - 1
            if px <= nx <= px + 2:
                dy = -1
                bounces += 1
                # Bord de raquette → inverse la direction horizontale
                if nx == px     and dx ==  1: dx = -1
                if nx == px + 2 and dx == -1: dx =  1
            else:
                draw(nx, ny, px)
                sleep_ms(400)
                game_over_anim()
                bx, by, dx, dy, px, bounces = reset()
                last_move = ticks_ms()
                last_pad  = ticks_ms()
                continue

        bx, by = nx, ny

    draw(bx, by, px)
    sleep_ms(20)
