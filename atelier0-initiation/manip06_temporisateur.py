# Manipulation 06 — Temporisateur d'éclairage (minuterie d'escalier)
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# Principe : on appuie sur le bouton → la LED s'allume pendant 2 secondes
# puis s'éteint toute seule. Si on réappuie pendant que c'est allumé,
# le compteur repart à zéro (la durée est prolongée).
#
# Méthode : un COMPTEUR qui démarre à 20 à chaque appui.
# À chaque tour de boucle (toutes les 0,1 s), le compteur descend de 1.
# La LED est allumée tant que le compteur est positif.
#   → 20 × 0,1 s = 2 secondes d'éclairage.
#
# C'est exactement le principe d'une minuterie d'escalier :
# on appuie → la lumière reste allumée un certain temps → elle s'éteint.
#
# Rien à brancher — LED GPIO 2, bouton BOOT GPIO 0.
# -----------------------------------------------------------------------

from machine import Pin
from time import sleep

led = Pin(2, Pin.OUT)
bp  = Pin(0, Pin.IN, Pin.PULL_UP)   # bouton BOOT, actif bas (0 = appuyé)

compt = 0                           # compteur de temporisation

print("Temporisateur — appuyer sur BOOT pour allumer 2 secondes")
print("Ctrl+C pour arrêter")

while True:
    # Si le bouton est appuyé (actif bas → value() == 0), relancer le compteur
    if bp.value() == 0:
        compt = 20                   # 20 itérations × 0,1 s = 2 secondes

    # La LED est allumée tant que le compteur est positif
    led.value(compt > 0)             # compt > 0 → True (1) → LED ON

    sleep(0.1)                       # chaque tour dure 0,1 seconde

    # Décrémenter le compteur, sans jamais passer en négatif
    if compt > 0:
        compt -= 1

# -----------------------------------------------------------------------
# COMMENT ÇA MARCHE :
#
#   compt = 20  →  led ON  →  sleep 0.1  →  compt = 19
#   compt = 19  →  led ON  →  sleep 0.1  →  compt = 18
#   ...
#   compt =  1  →  led ON  →  sleep 0.1  →  compt = 0
#   compt =  0  →  led OFF →  sleep 0.1  →  compt reste 0
#
# Si on appuie à compt = 5, le compteur remonte à 20 → relance le cycle.
#
# POURQUOI LE TEST "if compt > 0" :
#   Sans lui, le compteur continuerait à descendre : -1, -2, -3...
#   La LED resterait éteinte (le test compt > 0 serait faux), mais il
#   faudrait ensuite remonter depuis très loin pour la rallumer.
#   Le test bloque donc le compteur à 0.
#
#   Variante compacte que tu croiseras parfois :
#       compt -= (compt > 0)
#   Elle fonctionne car en Python True vaut 1 et False vaut 0.
#   C'est plus court, mais nettement moins lisible.
#
# VARIANTES À ESSAYER :
#   compt = 50   →  5 secondes d'éclairage
#   compt = 100  →  10 secondes
#   sleep(0.05)  →  plus de précision (doubler compt en conséquence)
# -----------------------------------------------------------------------
