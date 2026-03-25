# Manipulation 02 — Allumer et éteindre la LED intégrée
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# Toutes les cartes ESP32 ont une LED soudée directement sur la carte,
# connectée au GPIO 2 (broche numéro 2).
# On va la contrôler avec le module "machine" de MicroPython.
#
# GPIO = General Purpose Input Output
#        = Broche d'usage général, configurable en entrée ou en sortie
#
# Rien à brancher — la LED est déjà sur la carte.
# -----------------------------------------------------------------------

from machine import Pin    # on importe la classe Pin du module machine
                           # Pin = une broche (une patte) de l'ESP32

# Créer un objet "led" qui contrôle la broche GPIO 2, configurée en SORTIE
led = Pin(2, Pin.OUT)      # Pin.OUT = sortie (on envoie du courant)
                           # Pin.IN  = entrée (on lit un capteur, un bouton...)

# --- Allumer la LED ---
led.value(1)               # value(1) = mettre la broche à 3,3V → LED allumée
                           # équivalent : led.on()

# Pour éteindre, décommenter la ligne suivante :
# led.value(0)             # value(0) = mettre la broche à 0V → LED éteinte
                           # équivalent : led.off()

# -----------------------------------------------------------------------
# ESSAYER DANS LE SHELL (après avoir lancé ce fichier) :
#   >>> led.on()
#   >>> led.off()
#   >>> led.value(1)
#   >>> led.value(0)
#   >>> led.value()        # sans argument → lit l'état actuel (0 ou 1)
#
# À RETENIR :
#   - on() / value(1) → allumé   (3,3V sur la broche)
#   - off() / value(0) → éteint  (0V sur la broche)
#   - L'objet "led" reste disponible dans le Shell après l'exécution
# -----------------------------------------------------------------------
