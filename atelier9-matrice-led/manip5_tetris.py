from machine import Pin, SPI, TouchPad
from time import sleep_ms, ticks_ms
from random import randint

# --- Hardware ---
spi = SPI(2, baudrate=10_000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
cs  = Pin(5, Pin.OUT)
t_left  = TouchPad(Pin(4))   # D4  → gauche
t_right = TouchPad(Pin(15))  # D15 → droite  |  D4+D15 = rotation

SEUIL = 200
W, H = 8, 32  # 8 colonnes × 32 lignes

# --- MAX7219 init ---
def _cmd(reg, val):
    cs(0)
    for _ in range(4): spi.write(bytearray([reg, val]))
    cs(1)
for r, v in [(12,0),(15,0),(11,7),(9,0),(10,2),(12,1)]:
    _cmd(r, v)

buf = bytearray(H)

def show():  # transposé : game(gx=r, gy=chip*8+k) → physique vertical
    for r in range(8):
        cs(0)
        for chip in range(4):
            byte = 0
            for k in range(8):
                if buf[chip * 8 + k] & (0x80 >> r):
                    byte |= (0x80 >> k)
            spi.write(bytearray([1 + r, byte]))
        cs(1)

# --- Pièces : liste de rotations, chaque rotation = liste de (dx, dy) ---
PIECES = [
    [[(0,0),(0,1),(0,2),(0,3)],                             # I vert
     [(0,0),(1,0),(2,0),(3,0)]],                            # I horiz
    [[(0,0),(1,0),(0,1),(1,1)]],                            # O
    [[(1,0),(0,1),(1,1),(2,1)],                             # T
     [(0,0),(0,1),(1,1),(0,2)],
     [(0,0),(1,0),(2,0),(1,1)],
     [(1,0),(0,1),(1,1),(1,2)]],
    [[(1,0),(0,1),(1,1),(0,2)],                             # S
     [(0,0),(1,0),(1,1),(2,1)]],
    [[(0,0),(1,0),(1,1),(2,1)],                             # Z
     [(1,0),(0,1),(1,1),(0,2)]],
    [[(0,0),(0,1),(1,1),(2,1)],                             # J
     [(0,0),(1,0),(0,1),(0,2)],
     [(0,0),(1,0),(2,0),(2,1)],
     [(1,0),(1,1),(0,2),(1,2)]],
    [[(2,0),(0,1),(1,1),(2,1)],                             # L
     [(0,0),(0,1),(0,2),(1,2)],
     [(0,0),(1,0),(2,0),(0,1)],
     [(0,0),(1,0),(1,1),(1,2)]],
]

def cells(px, py, rot, p):
    rots = PIECES[p]
    return [(px + dx, py + dy) for dx, dy in rots[rot % len(rots)]]

def valid(px, py, rot, p, board):
    for x, y in cells(px, py, rot, p):
        if x < 0 or x >= W or y >= H: return False
        if y >= 0 and board[y] & (0x80 >> x): return False
    return True

def lock(px, py, rot, p, board):
    for x, y in cells(px, py, rot, p):
        if 0 <= y < H: board[y] |= (0x80 >> x)

def clear_lines(board):
    new = bytearray(H)
    dest = H - 1
    for src in range(H - 1, -1, -1):
        if board[src] != 0xFF:
            new[dest] = board[src]
            dest -= 1
    return new

def draw(board, px, py, rot, p):
    global buf
    buf = bytearray(board)
    for x, y in cells(px, py, rot, p):
        if 0 <= y < H: buf[y] |= (0x80 >> x)
    show()

def new_piece():
    p = randint(0, 6)
    return p, 0, 3, 0  # piece, rot, x, y

def game_over_anim():
    for y in range(H):
        buf[y] = 0xFF
        show()
        sleep_ms(30)
    sleep_ms(800)
    for y in range(H):
        buf[y] = 0
        show()
        sleep_ms(30)

# --- Jeu ---
board = bytearray(H)
piece, rot, px, py = new_piece()
fall_time = ticks_ms()
fall_ms = 600
prev_l = prev_r = False
both_since = None   # instant où D4+D15 ont été pressés ensemble

while True:
    now = ticks_ms()
    l = t_left.read()  < SEUIL
    r = t_right.read() < SEUIL

    if l and r:
        if both_since is None:
            both_since = now          # début appui simultané
        elif both_since != -1 and now - both_since >= 400:
            # Appui long → chute immédiate
            while valid(px, py + 1, rot, piece, board):
                py += 1
            both_since = -1           # marquer "déjà traité"
    else:
        if both_since is not None and both_since != -1 and now - both_since < 400:
            # Appui court → rotation
            new_rot = (rot + 1) % len(PIECES[piece])
            if valid(px, py, new_rot, piece, board): rot = new_rot
        both_since = None
        if l and not prev_l:
            if valid(px - 1, py, rot, piece, board): px -= 1
        elif r and not prev_r:
            if valid(px + 1, py, rot, piece, board): px += 1

    prev_l, prev_r = l, r

    # Chute automatique
    if now - fall_time > fall_ms:
        fall_time = now
        if valid(px, py + 1, rot, piece, board):
            py += 1
        else:
            lock(px, py, rot, piece, board)
            board = clear_lines(board)
            piece, rot, px, py = new_piece()
            if not valid(px, py, rot, piece, board):
                game_over_anim()
                board = bytearray(H)
                piece, rot, px, py = new_piece()

    draw(board, px, py, rot, piece)
    sleep_ms(40)
