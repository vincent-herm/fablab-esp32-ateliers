# Atelier 02 — E-paper — Manip 02 : premier affichage
# Fablab Ardèche — MicroPython
#
# On écrit « Bonjour » sur l'écran, puis on mesure combien de temps
# prend le rafraîchissement.
#
# Convention des couleurs : 0 = blanc, 1 = noir.
#
# Matériel : carte LilyGo T5 V2.3 (écran e-paper déjà câblé)

from gdeh0213b73 import init_epd, ROTATION_0
import time

epd = init_epd(rotation=ROTATION_0)   # portrait : 128 pixels de large, 250 de haut

epd.fill(0)                           # tout l'écran en blanc
epd.text("Bonjour", 10, 10, 1)        # texte noir, en haut à gauche
epd.text("Fablab Payzac", 10, 30, 1)
epd.rect(0, 0, epd.width, epd.height, 1)   # un cadre autour de l'écran

debut = time.ticks_ms()
epd.update()                          # rien n'apparaît avant cette ligne !
duree = time.ticks_diff(time.ticks_ms(), debut)
print("Rafraîchissement : {} ms".format(duree))

epd.deep_sleep()                      # l'image reste, l'écran ne consomme plus rien
