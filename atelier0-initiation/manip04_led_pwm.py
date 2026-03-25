# Manipulation 04 — LED qui "respire" avec le PWM
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# PWM = Pulse Width Modulation = Modulation de Largeur d'Impulsion
#
# Une broche numérique ne peut faire que 0V ou 3,3V — rien entre les deux.
# Le PWM simule un niveau intermédiaire en allumant/éteignant très vite
# la LED (des centaines de fois par seconde).
#
# Si la LED est allumée 50% du temps et éteinte 50% du temps,
# l'œil voit une luminosité à 50%. C'est le "duty cycle" (rapport cyclique).
#
#   duty = 0    → LED éteinte (0% du temps allumée)
#   duty = 512  → LED mi-luminosité (50% du temps allumée)
#   duty = 1023 → LED à pleine luminosité (100% du temps allumée)
#
# Rien à brancher — LED intégrée sur GPIO 2.
# -----------------------------------------------------------------------

from machine import Pin, PWM    # PWM est dans le même module que Pin
import time                     # pour les pauses

# Créer un objet PWM sur la broche GPIO 2
# freq=1000 signifie que la LED clignote 1000 fois par seconde
# (trop rapide pour que l'œil le voit — il perçoit juste la luminosité moyenne)
led = PWM(Pin(2), freq=1000)

print("LED qui respire — appuyer Ctrl+C pour arrêter")

# Boucle infinie : montée puis descente progressive
while True:
    # Montée : de 0 à 1023 par pas de 5
    for luminosite in range(0, 1023, 5):
        led.duty(luminosite)   # régler la luminosité
        time.sleep_ms(5)       # pause de 5 millisecondes entre chaque pas

    # Descente : de 1023 à 0 par pas de 5
    for luminosite in range(1023, 0, -5):
        led.duty(luminosite)
        time.sleep_ms(5)

# -----------------------------------------------------------------------
# EXPÉRIENCES À TESTER DANS LE SHELL (après Ctrl+C) :
#   >>> led.duty(0)      # éteinte
#   >>> led.duty(100)    # très faible
#   >>> led.duty(512)    # moitié
#   >>> led.duty(1023)   # pleine puissance
#
# À RETENIR :
#   - PWM permet de contrôler l'intensité lumineuse d'une LED
#   - PWM sert aussi à contrôler la vitesse d'un moteur ou la position
#     d'un servo-moteur (manips futures)
#   - sleep_ms(5) = pause de 5 millisecondes (plus précis que sleep(0.005))
# -----------------------------------------------------------------------
