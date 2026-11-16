from machine import Pin, I2C
from time import ticks_ms, ticks_diff, sleep_ms
from math import sin, cos, pi
from random import uniform, randint
import ssd1306

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400_000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

DUREE = 8000   # durée de chaque animation, en millisecondes


def fini(debut):
    return ticks_diff(ticks_ms(), debut) > DUREE


# --- 1. Sinusoïde et courbe de Lissajous -------------------------------------
def sinusoides():
    oled.fill(0)
    for x in range(128):                       # une période sur toute la largeur
        y = sin(x / 128 * 2 * pi)              # y va de -1 à 1
        oled.pixel(x, round(32 - 26 * y), 1)   # -1..1 devient 58..6
        oled.show()
    sleep_ms(1500)

    oled.fill(0)
    for t in range(360):                       # Lissajous : deux sinus combinés
        a = t / 360 * 2 * pi
        oled.pixel(round(64 + 50 * sin(2 * a)), round(32 - 26 * sin(3 * a)), 1)
        if t % 6 == 0:
            oled.show()
    oled.show()
    sleep_ms(2500)


# --- 2. Ondes qui défilent ---------------------------------------------------
def ondes():
    phase = 0.0
    debut = ticks_ms()
    while not fini(debut):
        oled.fill(0)
        for x in range(0, 128, 6):
            oled.pixel(x, 32, 1)               # axe central en pointillé
        for x in range(128):
            y1 = round(18 + 12 * sin(x / 11 + phase))
            y2 = round(46 + 12 * sin(x / 11 + phase + pi * 0.7))
            oled.vline(x, y1, 2, 1)
            oled.vline(x, y2, 2, 1)
        oled.show()
        phase += 0.16                          # décaler l'onde = la faire avancer


# --- 3. Champ d'étoiles -------------------------------------------------------
def etoiles():
    stars = [[uniform(-1, 1), uniform(-1, 1), uniform(0.1, 1)] for _ in range(60)]
    debut = ticks_ms()
    while not fini(debut):
        oled.fill(0)
        for s in stars:
            s[2] -= 0.028                      # l'étoile se rapproche
            if s[2] <= 0.02:                   # trop proche : on la renvoie au loin
                s[0], s[1], s[2] = uniform(-0.8, 0.8), uniform(-0.8, 0.8), 1.0
            px = round(64 + s[0] / s[2] * 58)  # plus elle est proche, plus elle s'écarte
            py = round(32 + s[1] / s[2] * 30)
            if 0 <= px < 127 and 0 <= py < 63:
                oled.pixel(px, py, 1)
                if s[2] < 0.4:                 # étoiles proches = plus grosses
                    oled.fill_rect(px, py, 2, 2, 1)
        oled.show()
        sleep_ms(20)


# --- 4. Pluie Matrix -----------------------------------------------------------
def matrix():
    COLS, LIGNES = 16, 8                       # 16 × 8 caractères de 8 pixels
    grille = [[' '] * COLS for _ in range(LIGNES)]
    tetes = [randint(-LIGNES, 0) for _ in range(COLS)]
    debut = ticks_ms()
    while not fini(debut):
        oled.fill(0)
        for c in range(COLS):
            tetes[c] += 1
            if 0 <= tetes[c] < LIGNES:
                grille[tetes[c]][c] = chr(randint(33, 90))
            if tetes[c] >= LIGNES + 2:         # colonne finie : on la vide
                tetes[c] = randint(-LIGNES, -2)
                for l in range(LIGNES):
                    grille[l][c] = ' '
            for l in range(LIGNES):
                if grille[l][c] != ' ':
                    oled.text(grille[l][c], c * 8, l * 8, 1)
        oled.show()
        sleep_ms(110)


# --- 5. Cube 3D ----------------------------------------------------------------
SOMMETS = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
           (-1, -1,  1), (1, -1,  1), (1, 1,  1), (-1, 1,  1)]
FACES = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
         (3, 2, 6, 7), (0, 3, 7, 4), (1, 2, 6, 5)]
TAILLE, DISTANCE, INCLINAISON = 17, 6, 0.5

def cube():
    ci, si = cos(INCLINAISON), sin(INCLINAISON)
    angle = 0.0
    debut = ticks_ms()
    while not fini(debut):
        ca, sa = cos(angle), sin(angle)
        espace, ecran = [], []
        for x, y, z in SOMMETS:
            x, z = x * ca - z * sa, x * sa + z * ca      # rotation sur lui-même
            y, z = y * ci - z * si, y * si + z * ci      # inclinaison vers toi
            espace.append((x, y, z))
            f = DISTANCE / (DISTANCE + z)                # perspective
            ecran.append((round(64 + x * TAILLE * f), round(32 + y * TAILLE * f)))
        oled.fill(0)
        for face in FACES:
            cx = sum(espace[i][0] for i in face) / 4
            cy = sum(espace[i][1] for i in face) / 4
            cz = sum(espace[i][2] for i in face) / 4
            if cz < -(cx * cx + cy * cy + cz * cz) / DISTANCE:   # face tournée vers toi
                for k in range(4):
                    a, b = ecran[face[k]], ecran[face[(k + 1) % 4]]
                    oled.line(a[0], a[1], b[0], b[1], 1)
        oled.show()
        angle += 0.04
        sleep_ms(20)


# --- Enchaînement ----------------------------------------------------------------
animations = [sinusoides, ondes, etoiles, matrix, cube]
while True:
    for animation in animations:
        animation()
