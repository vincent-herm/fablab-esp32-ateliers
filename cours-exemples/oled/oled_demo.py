# oled_demo.py — Animations OLED 1.3 pouces
# -----------------------------------------------------------------------
# Pins : SCL→22  SDA→21  3.3V  GND   bpA→25 (animation suivante)
#
# 4 animations :
#   1. Cube 3D tournant
#   2. Champ d'étoiles (warp speed)
#   3. Pluie Matrix
#   4. Double onde sinusoïdale
# -----------------------------------------------------------------------

from machine import I2C, Pin
from sh1106 import SH1106_I2C
from time import ticks_ms, sleep_ms
from math import sin, cos, pi
import random

i2c     = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
display = SH1106_I2C(128, 64, i2c)
bpA     = Pin(25, Pin.IN)

DUREE = 8000   # ms par animation

def temps_ecoule(t0):
    return ticks_ms() - t0 > DUREE or bpA.value()


# =============================================================================
# ANIMATION 1 — Cube 3D tournant
# =============================================================================

VERTICES = [
    (-1,-1,-1), (1,-1,-1), (1,1,-1), (-1,1,-1),
    (-1,-1, 1), (1,-1, 1), (1,1, 1), (-1,1, 1),
]
EDGES = [
    (0,1),(1,2),(2,3),(3,0),   # face avant
    (4,5),(5,6),(6,7),(7,4),   # face arrière
    (0,4),(1,5),(2,6),(3,7),   # arêtes reliant
]

def cube():
    ax, ay = 0.3, 0.5
    t0 = ticks_ms()
    while not temps_ecoule(t0):
        display.fill(0)
        pts = []
        for vx, vy, vz in VERTICES:
            # Rotation Y
            x = vx * cos(ay) - vz * sin(ay)
            z = vx * sin(ay) + vz * cos(ay)
            # Rotation X
            y2 = vy * cos(ax) - z * sin(ax)
            z2 = vy * sin(ax) + z * cos(ax)
            # Projection perspective
            fov = 3.5 / (z2 + 4.5)
            pts.append((int(x * 22 * fov + 64), int(y2 * 22 * fov + 32)))
        for a, b in EDGES:
            x1, y1 = pts[a]
            x2, y2 = pts[b]
            display.line(x1, y1, x2, y2, 1)
        display.show()
        ax += 0.026
        ay += 0.038
        sleep_ms(25)


# =============================================================================
# ANIMATION 2 — Champ d'étoiles (warp speed)
# =============================================================================

def starfield():
    N = 60
    stars = [
        [random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.1, 1)]
        for _ in range(N)
    ]
    t0 = ticks_ms()
    while not temps_ecoule(t0):
        display.fill(0)
        for s in stars:
            s[2] -= 0.028
            if s[2] <= 0.02:
                s[0] = random.uniform(-0.8, 0.8)
                s[1] = random.uniform(-0.8, 0.8)
                s[2] = 1.0
            px = int(s[0] / s[2] * 58 + 64)
            py = int(s[1] / s[2] * 30 + 32)
            if 0 <= px < 128 and 0 <= py < 64:
                display.pixel(px, py, 1)
                if s[2] < 0.4:   # étoiles proches = plus grandes
                    if px + 1 < 128: display.pixel(px + 1, py, 1)
                    if py + 1 < 64:  display.pixel(px, py + 1, 1)
        display.show()
        sleep_ms(25)


# =============================================================================
# ANIMATION 3 — Pluie Matrix
# =============================================================================

def matrix():
    NCOLS = 16                  # 16 colonnes × 8 px = 128 px
    NROWS = 8                   # 8 lignes × 8 px = 64 px
    grille = [[' '] * NCOLS for _ in range(NROWS)]
    heads  = [random.randint(-NROWS, 0) for _ in range(NCOLS)]
    t0 = ticks_ms()

    while not temps_ecoule(t0):
        display.fill(0)
        for col in range(NCOLS):
            heads[col] += 1
            row = heads[col]
            if 0 <= row < NROWS:
                grille[row][col] = chr(random.randint(33, 90))
            if heads[col] >= NROWS + 2:
                heads[col] = random.randint(-NROWS, -2)
                for r in range(NROWS):
                    grille[r][col] = ' '
            for r in range(NROWS):
                if grille[r][col] != ' ':
                    display.text(grille[r][col], col * 8, r * 8, 1)
        display.show()
        sleep_ms(110)


# =============================================================================
# ANIMATION 4 — Double onde sinusoïdale
# =============================================================================

def ondes():
    phase = 0.0
    t0 = ticks_ms()
    while not temps_ecoule(t0):
        display.fill(0)

        # Axe central pointillé
        for x in range(0, 128, 6):
            display.pixel(x, 32, 1)

        for x in range(128):
            # Onde du haut
            y1 = int(18 + 12 * sin(x / 11.0 + phase))
            # Onde du bas (symétrique + déphasée)
            y2 = int(46 + 12 * sin(x / 11.0 + phase + pi * 0.7))
            display.pixel(x, y1, 1)
            if y1 + 1 < 64: display.pixel(x, y1 + 1, 1)
            display.pixel(x, y2, 1)
            if y2 + 1 < 64: display.pixel(x, y2 + 1, 1)

        display.show()
        phase += 0.16
        sleep_ms(20)


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

animations = [cube, starfield, matrix, ondes]
noms       = ["Cube 3D", "Etoiles warp", "Matrix rain", "Ondes"]
idx        = 0

print("=== OLED Demo — bpA = animation suivante ===")

while True:
    print(f"→ {noms[idx]}")
    animations[idx]()
    while bpA.value():
        sleep_ms(10)
    idx = (idx + 1) % len(animations)
