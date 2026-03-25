# Manipulation 03 — Faire clignoter la LED (boucle infinie)
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# On combine la LED (manip 02) avec une boucle infinie et des pauses.
# C'est le "Hello World" de l'électronique embarquée.
#
# La fonction time.sleep() met le programme en pause un certain nombre
# de secondes. Pendant cette pause, l'ESP32 ne fait rien d'autre.
#
# Rien à brancher — LED intégrée sur GPIO 2.
# -----------------------------------------------------------------------

from machine import Pin    # pour contrôler les broches
import time                # pour les fonctions de pause (sleep)

# Initialisation de la LED sur GPIO 2 en sortie
led = Pin(2, Pin.OUT)

print("LED qui clignote — appuyer Ctrl+C pour arrêter")

# Boucle infinie : while True tourne indéfiniment jusqu'à Ctrl+C
while True:
    led.value(1)           # allumer la LED
    time.sleep(0.5)        # pause 0,5 seconde (500 ms)
    led.value(0)           # éteindre la LED
    time.sleep(0.5)        # pause 0,5 seconde

# -----------------------------------------------------------------------
# EXPÉRIENCES À TESTER :
#   - Changer 0.5 en 0.1 → clignotement rapide
#   - Changer 0.5 en 2.0 → clignotement lent
#   - Mettre des durées différentes : 0.1 allumé, 0.9 éteint
#     (comme un phare ou un signal morse)
#
# POUR ARRÊTER :
#   - Appuyer Ctrl+C dans Thonny → KeyboardInterrupt
#
# VERSION COMPACTE (même résultat, une seule ligne dans la boucle) :
#   while True:
#       led.value(not led.value())   # inverse l'état actuel
#       time.sleep(0.5)
# -----------------------------------------------------------------------
