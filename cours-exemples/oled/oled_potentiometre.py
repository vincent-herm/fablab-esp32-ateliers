# oled_potentiometre.py — OLED 1.3" + potentiomètre
# -----------------------------------------------------------------------
# Pins : SCL→22  SDA→21  3.3V  GND
#        Pot→35 (broche centrale)   bpA→25 (animation suivante)
#
# 4 animations — le potentiomètre contrôle un paramètre en temps réel :
#   1. Cube 3D       → vitesse de rotation (lent ↔ rapide)
#   2. Lissajous     → ratio B/A  (1=cercle  2=huit  3=trèfle  4=nœud  5=étoile)
#   3. Tunnel infini → vitesse de défilement
#   4. Égaliseur     → énergie / amplitude des barres
#
# Indicateur en bas de l'écran (barre fine) = position du potentiomètre
# -----------------------------------------------------------------------

from machine import I2C, Pin, ADC
from sh1106 import SH1106_I2C
from time import ticks_ms, sleep_ms
from math import sin, cos, pi
import random

i2c     = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
display = SH1106_I2C(128, 64, i2c)

pot = ADC(Pin(35))
pot.atten(ADC.ATTN_11DB)
pot.width(ADC.WIDTH_9BIT)   # 0 – 511

bpA = Pin(25, Pin.IN)

DUREE = 10000   # ms par animation

def pot_val():
    """Valeur normalisée 0.0 → 1.0"""
    return pot.read() / 511.0

def temps_ecoule(t0):
    return ticks_ms() - t0 > DUREE or bpA.value()

def barre_pot(v):
    """Fine barre indicatrice en bas de l'écran"""
    w = int(v * 126)
    display.fill_rect(0, 62, w, 2, 1)


# =============================================================================
# ANIMATION 1 — Cube 3D  (pot = vitesse de rotation)
# =============================================================================

VERTICES = [
    (-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
    (-1,-1, 1),(1,-1, 1),(1,1, 1),(-1,1, 1),
]
EDGES = [
    (0,1),(1,2),(2,3),(3,0),
    (4,5),(5,6),(6,7),(7,4),
    (0,4),(1,5),(2,6),(3,7),
]

def cube():
    ax, ay = 0.0, 0.0
    t0 = ticks_ms()
    while not temps_ecoule(t0):
        v   = pot_val()
        spd = v * 0.09 + 0.004   # 0.004 (lent) → 0.094 (rapide)
        display.fill(0)
        pts = []
        for vx, vy, vz in VERTICES:
            x  = vx * cos(ay) - vz * sin(ay)
            z  = vx * sin(ay) + vz * cos(ay)
            y2 = vy * cos(ax) - z  * sin(ax)
            z2 = vy * sin(ax) + z  * cos(ax)
            fov = 3.5 / (z2 + 4.5)
            pts.append((int(x * 22 * fov + 64), int(y2 * 22 * fov + 30)))
        for a, b in EDGES:
            display.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], 1)
        barre_pot(v)
        display.show()
        ax += spd * 0.7
        ay += spd
        sleep_ms(20)


# =============================================================================
# ANIMATION 2 — Courbes de Lissajous  (pot = ratio B/A)
# =============================================================================

def lissajous():
    t0    = ticks_ms()
    phase = 0.0
    while not temps_ecoule(t0):
        v     = pot_val()
        ratio = int(v * 4) + 1   # 1, 2, 3, 4 ou 5
        display.fill(0)
        display.text(f"B/A = {ratio}", 36, 0, 1)
        prev_x = prev_y = None
        for i in range(201):
            t = 2 * pi * i / 200
            x = int(58 * sin(t + phase) + 64)
            y = int(26 * sin(ratio * t) + 34)
            if 0 <= x < 128 and 0 <= y < 62:
                if prev_x is not None:
                    display.line(prev_x, prev_y, x, y, 1)
                prev_x, prev_y = x, y
        barre_pot(v)
        display.show()
        phase += 0.05
        sleep_ms(30)


# =============================================================================
# ANIMATION 3 — Tunnel infini  (pot = vitesse de défilement)
# =============================================================================

def tunnel():
    t0    = ticks_ms()
    depth = 0.0
    CX, CY = 64, 30
    while not temps_ecoule(t0):
        v   = pot_val()
        spd = v * 0.04 + 0.003
        display.fill(0)
        for i in range(10):
            z = ((i / 10.0) + depth) % 1.0
            if z < 0.06:
                continue
            w = int(z * 58)
            h = int(z * 26)
            display.rect(CX - w, CY - h, w * 2, h * 2, 1)
        # Croix centrale
        display.line(CX - 5, CY, CX + 5, CY, 1)
        display.line(CX, CY - 5, CX, CY + 5, 1)
        barre_pot(v)
        display.show()
        depth = (depth + spd) % 1.0
        sleep_ms(20)


# =============================================================================
# ANIMATION 4 — Égaliseur  (pot = énergie / amplitude)
# =============================================================================

def egaliseur():
    N    = 16
    hts  = [float(random.randint(2, 8)) for _ in range(N)]
    vels = [0.0] * N
    t0   = ticks_ms()
    while not temps_ecoule(t0):
        v     = pot_val()
        max_h = int(v * 52 + 4)   # 4 px min → 56 px max
        display.fill(0)
        for i in range(N):
            target   = random.randint(int(max_h * 0.3), max_h)
            vels[i] += (target - hts[i]) * 0.1 + random.uniform(-0.4, 0.4)
            vels[i]  = max(-3.0, min(3.0, vels[i]))
            hts[i]  += vels[i]
            hts[i]   = max(2.0, min(float(max_h), hts[i]))
            h = int(hts[i])
            display.fill_rect(i * 8, 60 - h, 7, h, 1)
        barre_pot(v)
        display.show()
        sleep_ms(40)


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

animations = [cube, lissajous, tunnel, egaliseur]
noms       = ["Cube 3D", "Lissajous", "Tunnel", "Egaliseur"]
idx        = 0

print("=== OLED + Potentiometre ===")
print("Pot Pin 35  — controle l'animation en cours")
print("bpA Pin 25  — animation suivante")

while True:
    print(f"-> {noms[idx]}")
    animations[idx]()
    while bpA.value():
        sleep_ms(10)
    idx = (idx + 1) % len(animations)
