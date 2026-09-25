# Atelier 02 — Aller plus loin n°6 : chenillard qui rebondit, avec traînée
# Fablab Ardèche — MicroPython
#
# Le défi de la page « Toi de jouer » : un point rouge fait des allers-retours
# et laisse derrière lui une traînée qui s'éteint doucement (effet K2000).
# Le bouton change la vitesse (lente / moyenne / rapide).
#
# Matériel : ESP32 + bandeau NeoPixel 16 LED + 1 bouton poussoir
# Connexions : DATA → GPIO18, bouton (BP) entre GPIO5 et GND

from machine import Pin
from neopixel import NeoPixel
import time

N = 16
np = NeoPixel(Pin(18, Pin.OUT), N)
bp = Pin(5, Pin.IN, Pin.PULL_UP)

VITESSES = [("lente", 80), ("moyenne", 40), ("rapide", 15)]
vitesse_idx = 1

pos, sens = 0, 1
print("Appuie sur le bouton pour changer de vitesse")

while True:
    # 1) toutes les LEDs s'atténuent (on garde les 2/3 de leur valeur)
    for i in range(N):
        r, v, b = np[i]
        np[i] = (r * 2 // 3, v * 2 // 3, b * 2 // 3)
    # 2) la tête est allumée à fond
    np[pos] = (255, 0, 0)
    np.write()

    # 3) rebond aux deux extrémités
    if pos + sens < 0 or pos + sens >= N:
        sens = -sens
    pos += sens

    time.sleep_ms(VITESSES[vitesse_idx][1])

    if bp.value() == 0:
        vitesse_idx = (vitesse_idx + 1) % len(VITESSES)
        print("Vitesse :", VITESSES[vitesse_idx][0])
        while bp.value() == 0:
            time.sleep_ms(10)
