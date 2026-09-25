# Atelier 02 — Aller plus loin n°2 : compteur binaire
# Fablab Ardèche — MicroPython
#
# Chaque appui court sur le bouton ajoute 1. Le bandeau affiche le nombre
# en binaire : LED allumée = bit à 1. LED 0 = poids faible (1), LED 7 = 128.
# Appui long (plus de 0,8 s) : remise à zéro.
#
# Matériel : ESP32 + bandeau NeoPixel 8 LED + 1 bouton poussoir
# Connexions : DATA → GPIO18, bouton (BP) entre GPIO5 et GND

from machine import Pin
from neopixel import NeoPixel
import time

N = 8
np = NeoPixel(Pin(18, Pin.OUT), N)
bp = Pin(5, Pin.IN, Pin.PULL_UP)


def afficher(valeur):
    for i in range(N):
        if (valeur >> i) & 1:           # le bit i vaut-il 1 ?
            np[i] = (0, 20, 60)
        else:
            np[i] = (0, 0, 0)
    np.write()
    print(valeur, "=", "{:08b}".format(valeur))


valeur = 0
afficher(valeur)
print("Appui court : +1   |   appui long : remise à zéro")

while True:
    if bp.value() == 0:
        t0 = time.ticks_ms()
        time.sleep_ms(30)               # anti-rebond
        while bp.value() == 0:
            time.sleep_ms(10)
        duree = time.ticks_diff(time.ticks_ms(), t0)
        if duree > 800:
            valeur = 0
        else:
            valeur = (valeur + 1) % 256
        afficher(valeur)
        time.sleep_ms(30)
    time.sleep_ms(10)
