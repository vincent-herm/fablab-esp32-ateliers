# Atelier 02 — Aller plus loin n°4 : dé électronique
# Fablab Ardèche — MicroPython
#
# Appuie sur le bouton pour lancer le dé. Le bandeau tire des valeurs au hasard
# de plus en plus lentement (comme un dé qui ralentit), puis s'arrête sur
# le résultat : le nombre de LEDs allumées, de 1 à 6.
#
# Matériel : ESP32 + bandeau NeoPixel 8 LED + 1 bouton poussoir
# Connexions : DATA → GPIO18, bouton (BP) entre GPIO5 et GND

from machine import Pin
from neopixel import NeoPixel
import time
import random

N = 8
np = NeoPixel(Pin(18, Pin.OUT), N)
bp = Pin(5, Pin.IN, Pin.PULL_UP)


def afficher(valeur, couleur):
    """Allume les 'valeur' premières LEDs."""
    for i in range(N):
        np[i] = couleur if i < valeur else (0, 0, 0)
    np.write()


def lancer():
    delai = 40
    valeur = 1
    while delai < 400:
        valeur = random.randint(1, 6)
        afficher(valeur, (0, 30, 60))
        time.sleep_ms(delai)
        delai = int(delai * 1.25)       # ralentit à chaque tirage
    afficher(valeur, (255, 60, 0))      # résultat final en orange
    print("Résultat :", valeur)


afficher(0, (0, 0, 0))
print("Appuie sur le bouton pour lancer le dé")

while True:
    if bp.value() == 0:
        lancer()
        while bp.value() == 0:
            time.sleep_ms(10)
        time.sleep_ms(50)
    time.sleep_ms(10)
