# Atelier 02 — E-paper — Manip 07 : un compteur avec le bouton
# Fablab Ardèche — MicroPython
#
# Chaque appui sur le bouton ajoute 1 et redessine le nombre en très gros.
# Observe : l'écran met environ 2 secondes à se rafraîchir. Pendant ce temps,
# les appuis sont ignorés. C'est le prix de l'e-paper : zéro consommation
# pour garder l'image, mais un affichage lent.
#
# Matériel : carte LilyGo T5 V2.3 (écran e-paper déjà câblé)
# Bouton : celui de la carte, sur GPIO39.

from machine import Pin
from gdeh0213b73 import init_epd, ROTATION_90
import framebuf
import time

BOUTON = 39                           # GPIO39 : bouton de la carte T5
bp = Pin(BOUTON, Pin.IN)              # GPIO39 n'a pas de résistance de rappel interne
REPOS = bp.value()                    # état du bouton au repos, mesuré au démarrage


def appuye():
    return bp.value() != REPOS


def big_text(epd, s, x, y, scale=2, c=1):
    w = len(s) * 8
    buf = bytearray(((w + 7) // 8) * 8)
    fb = framebuf.FrameBuffer(buf, w, 8, framebuf.MONO_HLSB)
    fb.fill(0)
    fb.text(s, 0, 0, 1)
    for ty in range(8):
        for tx in range(w):
            if fb.pixel(tx, ty):
                epd.fill_rect(x + tx * scale, y + ty * scale, scale, scale, c)


def texte_centre(epd, s, y, scale=2, c=1):
    largeur = len(s) * 8 * scale
    big_text(epd, s, (epd.width - largeur) // 2, y, scale, c)


def afficher(epd, valeur):
    epd.fill(0)
    epd.rect(0, 0, epd.width, epd.height, 1)
    epd.text("Appuis sur le bouton :", 10, 10, 1)
    texte_centre(epd, str(valeur), 40, scale=8)      # chiffres de 64 pixels
    epd.update()


# On ne met PAS l'écran en deep_sleep entre deux affichages : il faudrait le
# réveiller avec un reset matériel.
epd = init_epd(rotation=ROTATION_90)
compteur = 0
afficher(epd, compteur)
print("Appuie sur le bouton (l'écran met ~2 s à se mettre à jour)")

while True:
    if appuye():
        compteur += 1
        print("Compteur :", compteur)
        afficher(epd, compteur)
        while appuye():                 # attendre le relâchement
            time.sleep_ms(10)
    time.sleep_ms(20)
