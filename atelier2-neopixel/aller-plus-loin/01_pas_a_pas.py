# Atelier 02 — Aller plus loin n°1 : la LED qui avance à chaque appui
# Fablab Ardèche — MicroPython
#
# Chaque appui sur le bouton fait avancer d'un cran la LED allumée.
#
# Matériel : ESP32 + bandeau NeoPixel 16 LED + 1 bouton poussoir
# Connexions : DATA → GPIO18, bouton (BP) entre GPIO5 et GND

from machine import Pin
from neopixel import NeoPixel
import time

N = 16
np = NeoPixel(Pin(18, Pin.OUT), N)
bp = Pin(5, Pin.IN, Pin.PULL_UP)

COULEUR = (0, 40, 120)      # bleu, pas trop éblouissant


def afficher(i):
    for k in range(N):
        np[k] = (0, 0, 0)
    np[i] = COULEUR
    np.write()


position = 0
afficher(position)
print("Appuie sur le bouton pour faire avancer la LED")

while True:
    if bp.value() == 0:                 # bouton enfoncé (actif à l'état bas)
        position = (position + 1) % N
        afficher(position)
        time.sleep_ms(30)               # anti-rebond
        while bp.value() == 0:          # attendre le relâchement
            time.sleep_ms(10)
        time.sleep_ms(30)
    time.sleep_ms(5)
