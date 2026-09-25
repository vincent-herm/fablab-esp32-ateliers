# Atelier 02 — Aller plus loin n°3 : jeu de réflexes
# Fablab Ardèche — MicroPython
#
# Un point bleu fait des allers-retours sur le bandeau. La LED du milieu
# est repérée en vert. Appuie sur BOOT au moment précis où le point passe
# dessus (il devient alors turquoise) !
#   - gagné : éclairs verts, et le point va plus vite
#   - raté  : éclairs rouges, retour à la vitesse de départ
#
# Matériel : ESP32 + bandeau NeoPixel 8 LED (rien de plus)
# Connexions : DATA → GPIO26, bouton BOOT = GPIO0

from machine import Pin
from neopixel import NeoPixel
import time

N = 8
CIBLE = N // 2
DELAI_DEPART = 140      # ms entre deux pas : plus petit = plus rapide
DELAI_MIN = 40

np = NeoPixel(Pin(26, Pin.OUT), N)
bp = Pin(0, Pin.IN, Pin.PULL_UP)


def tout_eteindre():
    for i in range(N):
        np[i] = (0, 0, 0)


def afficher(pos):
    tout_eteindre()
    np[CIBLE] = (0, 25, 0)                              # repère vert
    np[pos] = (0, 60, 60) if pos == CIBLE else (0, 0, 70)
    np.write()


def eclairs(couleur):
    for _ in range(3):
        for i in range(N):
            np[i] = couleur
        np.write()
        time.sleep_ms(120)
        tout_eteindre()
        np.write()
        time.sleep_ms(120)


def attendre(delai):
    """Attend delai ms. Renvoie True si BOOT est appuyé pendant ce temps."""
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < delai:
        if bp.value() == 0:
            return True
        time.sleep_ms(5)
    return False


delai = DELAI_DEPART
score = 0
pos, sens = 0, 1
print("Appuie sur BOOT quand le point passe sur la LED verte")

while True:
    afficher(pos)
    if attendre(delai):
        if pos == CIBLE:
            score += 1
            delai = max(DELAI_MIN, delai - 15)
            print("Gagné ! Score :", score)
            eclairs((0, 120, 0))
        else:
            print("Raté... score final :", score)
            score = 0
            delai = DELAI_DEPART
            eclairs((150, 0, 0))
        while bp.value() == 0:          # attendre le relâchement
            time.sleep_ms(10)
        time.sleep_ms(200)
    # avancer, en rebondissant aux deux bouts
    if pos + sens < 0 or pos + sens >= N:
        sens = -sens
    pos += sens
