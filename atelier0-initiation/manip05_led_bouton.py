# Manipulation 06 — La LED obéit au bouton (entrée → sortie)
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# On combine les deux manips précédentes :
#   - Bouton BOOT sur GPIO 0 (entrée)
#   - LED intégrée sur GPIO 2 (sortie)
#
# Le programme lit en permanence l'état du bouton et allume ou éteint
# la LED en conséquence. C'est la base de tout automatisme :
#   un CAPTEUR commande un ACTIONNEUR.
#
# Attention à la logique inversée du bouton :
#   bouton.value() == 0  →  bouton APPUYÉ   →  LED ALLUMÉE
#   bouton.value() == 1  →  bouton RELÂCHÉ  →  LED ÉTEINTE
#
# Rien à brancher — bouton et LED sont déjà sur la carte.
# -----------------------------------------------------------------------

from machine import Pin    # pour contrôler les broches
import time                # pour les pauses

# Initialisation des broches
led    = Pin(2, Pin.OUT)              # LED en sortie sur GPIO 2
bouton = Pin(0, Pin.IN, Pin.PULL_UP)  # bouton BOOT en entrée sur GPIO 0

print("Maintenez le bouton BOOT appuyé pour allumer la LED")
print("Appuyer Ctrl+C pour arrêter")

while True:
    if bouton.value() == 0:    # bouton appuyé (logique active bas)
        led.value(1)           # allumer la LED
    else:                      # bouton relâché
        led.value(0)           # éteindre la LED

    time.sleep(0.02)           # pause 20 ms — anti-rebond simple

# -----------------------------------------------------------------------
# VERSION UNE LIGNE (même résultat, plus compact) :
#   while True:
#       led.value(not bouton.value())   # not inverse : 0→1, 1→0
#       time.sleep(0.02)
#
# POUR ALLER PLUS LOIN :
#   Modifier le code pour que le bouton BASCULE la LED à chaque appui
#   (appui 1 → allume, appui 2 → éteint, appui 3 → allume...)
#   C'est ce qu'on appelle un "bascule" ou "flip-flop".
# -----------------------------------------------------------------------
