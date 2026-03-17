# Atelier 02 — LED RGB et NeoPixel (WS2812)
# Fablab Ardèche — MicroPython
#
# Contrôle un bandeau de 8 LED RGB WS2812.
# Les boutons changent l'animation en cours.
#
# Matériel : ESP32, bandeau NeoPixel 8 LED
# Connexions : DATA → GPIO26, BP_A → GPIO0 (PULL_UP)

from machine import Pin
from neopixel import NeoPixel
import time, random

# --- Configuration ---
N       = 8        # nombre de LEDs
NP_PIN  = 26
BP_PIN  = 0        # bouton BOOT (PULL_UP)

np = NeoPixel(Pin(NP_PIN, Pin.OUT), N)
bp = Pin(BP_PIN, Pin.IN, Pin.PULL_UP)

# --- Utilitaires couleur ---
def eteindre():
    for i in range(N):
        np[i] = (0, 0, 0)
    np.write()

def roue(pos):
    """Convertit 0-255 en couleur arc-en-ciel RGB."""
    pos = pos % 256
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    else:
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)

# --- Animations ---
def animation_defilement(couleur=(0, 80, 255), delai=80):
    """Une LED qui se déplace de gauche à droite."""
    for i in range(N):
        eteindre()
        np[i] = couleur
        np.write()
        time.sleep_ms(delai)
        if bp.value() == 0:
            return

def animation_arc_en_ciel(tours=3):
    """Arc-en-ciel qui défile sur toutes les LEDs."""
    for _ in range(tours * 256):
        for i in range(N):
            np[i] = roue((i * 32 + _) % 256)
        np.write()
        time.sleep_ms(15)
        if bp.value() == 0:
            return

def animation_scintillement(duree_ms=3000):
    """LEDs qui s'allument et s'éteignent aléatoirement."""
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < duree_ms:
        i = random.randint(0, N - 1)
        np[i] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        np.write()
        time.sleep_ms(80)
        np[i] = (0, 0, 0)
        np.write()
        if bp.value() == 0:
            return

def animation_remplissage(couleur=(255, 50, 0), delai=120):
    """Les LEDs s'allument une par une puis s'éteignent."""
    for i in range(N):
        np[i] = couleur
        np.write()
        time.sleep_ms(delai)
        if bp.value() == 0:
            return
    time.sleep_ms(400)
    for i in range(N - 1, -1, -1):
        np[i] = (0, 0, 0)
        np.write()
        time.sleep_ms(delai)
        if bp.value() == 0:
            return

# --- Boucle principale ---
animations = [
    ("Défilement bleu",    lambda: animation_defilement((0, 80, 255))),
    ("Défilement rouge",   lambda: animation_defilement((255, 30, 0))),
    ("Arc-en-ciel",        animation_arc_en_ciel),
    ("Scintillement",      animation_scintillement),
    ("Remplissage orange", lambda: animation_remplissage((255, 50, 0))),
    ("Remplissage vert",   lambda: animation_remplissage((0, 200, 50))),
]

idx = 0
print("Appuie sur le bouton BOOT pour changer d'animation")

while True:
    nom, anim = animations[idx]
    print(f"Animation : {nom}")
    anim()

    # Attendre que le bouton soit relâché
    while bp.value() == 0:
        time.sleep_ms(20)
    time.sleep_ms(100)

    idx = (idx + 1) % len(animations)
    eteindre()
