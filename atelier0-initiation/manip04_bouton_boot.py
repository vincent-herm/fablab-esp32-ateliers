# Manipulation 05 — Lire le bouton BOOT (entrée numérique)
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# Toutes les cartes ESP32 ont un bouton physique appelé "BOOT" (ou "IO0"),
# connecté au GPIO 0. On va lire son état.
#
# Logique inversée (pull-up) :
#   - Bouton RELÂCHÉ → la broche lit 1 (3,3V)
#   - Bouton APPUYÉ  → la broche lit 0 (0V, reliée à la masse)
#
# C'est la logique "active bas" : l'action donne 0, le repos donne 1.
# Elle est très courante en électronique.
#
# Rien à brancher — le bouton BOOT est déjà sur la carte.
# -----------------------------------------------------------------------

from machine import Pin    # pour contrôler les broches
import time                # pour les pauses

# Initialisation du bouton BOOT sur GPIO 0 en ENTRÉE avec résistance pull-up
# Pin.PULL_UP active une résistance interne qui maintient la broche à 3,3V
# quand rien n'est connecté (évite les lectures parasites)
bouton = Pin(0, Pin.IN, Pin.PULL_UP)

print("Lecture du bouton BOOT — appuyer Ctrl+C pour arrêter")
print("Appuyez sur le bouton BOOT pour voir la valeur changer...")

while True:
    etat = bouton.value()  # lire l'état : 1 = relâché, 0 = appuyé

    if etat == 0:          # bouton appuyé (logique inversée)
        print("APPUYÉ  → valeur =", etat)
    else:                  # bouton relâché
        print("relâché → valeur =", etat)

    time.sleep(0.2)        # pause 200 ms pour ne pas inonder la console

# -----------------------------------------------------------------------
# À RETENIR :
#   - Pin.IN  = broche configurée en entrée (on lit)
#   - Pin.OUT = broche configurée en sortie (on écrit)
#   - Pin.PULL_UP = résistance interne vers 3,3V (évite les flottements)
#   - Logique active bas : 0 = action, 1 = repos
#
# DANS LE SHELL :
#   >>> bouton.value()     # lire l'état instantané
# -----------------------------------------------------------------------
