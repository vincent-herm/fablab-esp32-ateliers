# Atelier 02 — Aller plus loin n°5 : veilleuse qui respire
# Fablab Ardèche — MicroPython
#
# Tout le bandeau « respire » (la luminosité monte et descend en douceur).
#   - appui COURT sur le bouton : couleur suivante
#   - appui LONG (plus de 0,6 s) : intensité maximale suivante (25 %, 50 %, 100 %)
#
# Matériel : ESP32 + bandeau NeoPixel 16 LED + 1 bouton poussoir
# Connexions : DATA → GPIO18, bouton (BP) entre GPIO5 et GND

from machine import Pin
from neopixel import NeoPixel
import time

N = 16
np = NeoPixel(Pin(18, Pin.OUT), N)
bp = Pin(5, Pin.IN, Pin.PULL_UP)

COULEURS = [
    ("orange", (255, 80, 0)),
    ("bleu",   (0, 60, 255)),
    ("vert",   (0, 220, 60)),
    ("violet", (150, 0, 200)),
    ("rose",   (255, 20, 80)),
]
INTENSITES = [1, 2, 4]          # 1 → 25 %, 2 → 50 %, 4 → 100 %

couleur_idx = 0
intensite_idx = 1
phase = 0                       # 0 à 99 : position dans la respiration
appui_debut = None

print("Appui court : couleur   |   appui long : intensité")

while True:
    # --- respiration : onde triangulaire 0 → 50 → 0 ---
    niveau = phase if phase < 50 else 100 - phase
    phase = (phase + 1) % 100
    facteur = niveau * INTENSITES[intensite_idx]        # 0 à 200
    r, v, b = COULEURS[couleur_idx][1]
    teinte = (r * facteur // 200, v * facteur // 200, b * facteur // 200)
    for i in range(N):
        np[i] = teinte
    np.write()

    # --- bouton : on mesure la durée de l'appui ---
    if bp.value() == 0:
        if appui_debut is None:
            appui_debut = time.ticks_ms()
    elif appui_debut is not None:
        duree = time.ticks_diff(time.ticks_ms(), appui_debut)
        appui_debut = None
        if duree > 600:
            intensite_idx = (intensite_idx + 1) % len(INTENSITES)
            print("Intensité :", INTENSITES[intensite_idx] * 25, "%")
        elif duree > 30:
            couleur_idx = (couleur_idx + 1) % len(COULEURS)
            print("Couleur :", COULEURS[couleur_idx][0])

    time.sleep_ms(20)
