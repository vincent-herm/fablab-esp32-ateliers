# =============================================================================
# ascenseur_enim_led.py — Simulation d'ascenseur sur carte ENIM (sans OLED)
# =============================================================================
# Version allégée : affichage uniquement sur le bandeau NeoPixel.
#
# CORRESPONDANCE CARTE ENIM ↔ ASCENSEUR :
#
#   Entrées :
#     bpA  (Pin 25) → bouton Start
#     bpB  (Pin 34) → fin de course HAUT
#     bpC  (Pin 39) → fin de course BAS
#
#   Sorties :
#     led_bleue (Pin  2) → témoin étape 0 (repos)
#     led_verte (Pin 18) → commande Descente
#     led_jaune (Pin 19) → commande Montée
#     np        (Pin 26) → indicateur de niveau (barre NeoPixel 8 LEDs)
#     Pin 12             → sortie réelle Descente (driver moteur / relais)
#     Pin 13             → sortie réelle Montée   (driver moteur / relais)
#
# GRAFCET (3 étapes) :
#
#       ┌──────────────────────────────────────┐
#       │  ÉTAPE 0 — Repos                     │  led_bleue allumée
#       └──────────────────┬───────────────────┘
#                          │ T0 : bpA pressé ET tempo[0] > 200 ms
#       ┌──────────────────▼───────────────────┐
#       │  ÉTAPE 1 — Descente                  │  led_verte allumée
#       └──────────────────┬───────────────────┘
#                          │ T1 : bpC actif OU niveau simulé ≤ -99
#       ┌──────────────────▼───────────────────┐
#       │  ÉTAPE 2 — Montée                    │  led_jaune allumée
#       └──────────────────┬───────────────────┘
#                          │ T2 : bpB actif OU niveau simulé ≥ -1
#                          └────────────────────────────► ÉTAPE 0
# =============================================================================

from machine import Pin
from grafcet  import Grafcet

from essential import (
    synchro_ms,    # synchronisation cycle 20 ms
    bpA,           # bouton Start          (Pin 25)
    bpB,           # fin de course HAUT    (Pin 34)
    bpC,           # fin de course BAS     (Pin 39)
    led_bleue,     # témoin repos          (Pin  2)
    led_verte,     # commande Descente     (Pin 18)
    led_jaune,     # commande Montée       (Pin 19)
    np,            # NeoPixel 8 LEDs       (Pin 26)
)

# Broches libres pour un vrai moteur (optionnel)
sortie_descente = Pin(12, Pin.OUT)   # driver moteur / relais Descente
sortie_montee   = Pin(13, Pin.OUT)   # driver moteur / relais Montée

# Sécurité : sorties moteur à 0 au démarrage
sortie_descente.value(0)
sortie_montee.value(0)

# NeoPixel éteint au démarrage
for led in range(8):
    np[led] = (0, 0, 0)
np.write()


# =============================================================================
# INITIALISATION DU MOTEUR GRAFCET
# =============================================================================

g = Grafcet(nb_etapes=3, etape_initiale=0)

T = [
    (0, (0,), (1,)),   # T0 : Repos → Descente
    (1, (1,), (2,)),   # T1 : Descente → Montée
    (2, (2,), (0,)),   # T2 : Montée → Repos
]


# =============================================================================
# VARIABLES
# =============================================================================

Descendre = False
Monter    = False
Start     = False
Haut      = False
Bas       = False

niveau   = 0      # position simulée : 0 = haut, -100 = bas
vitesse  = 1      # déplacement par cycle
x_ancien = 0      # dernière position NeoPixel affichée

transitions = [False] * len(T)


# =============================================================================
# SIMULATION DU NIVEAU — NeoPixel uniquement
# =============================================================================

def ascenseur(inc):
    """
    Déplace la cabine simulée et met à jour le bandeau NeoPixel.
    :param inc: -vitesse = descente, +vitesse = montée
    """
    global niveau, x_ancien

    # Déplacement avec butées
    niveau = niveau + inc
    if niveau < -100: niveau = -100    # plancher
    if niveau >    0: niveau =    0    # plafond

    # Conversion en position NeoPixel (0 = haut, 7 = bas)
    x = abs(int(-niveau / 12.6))

    # Rafraîchissement uniquement si la position a changé
    if x != x_ancien:
        for led in range(0, x): np[led] = (0, 30, 0)    # sous la cabine : vert
        for led in range(x, 8): np[led] = (0,  0, 0)    # au-dessus : éteint
        np[x] = (0, 50, 0)                               # position cabine : vert vif
        np.write()
        x_ancien = x


# =============================================================================
# CYCLE GRAFCET
# =============================================================================

def gerer_actions():
    global Descendre, Monter
    if g.etapes[0]: Descendre = False ; Monter = False    # Repos
    if g.etapes[1]: Descendre = True  ; Monter = False    # Descente
    if g.etapes[2]: Descendre = False ; Monter = True     # Montée


def affecter_sorties():
    led_bleue.value(g.etapes[0])         # témoin repos
    led_verte.value(Descendre)           # LED descente
    led_jaune.value(Monter)              # LED montée
    sortie_descente.value(Descendre)     # sortie moteur Descente
    sortie_montee.value(Monter)          # sortie moteur Montée
    if Descendre: ascenseur(-vitesse)    # simulation descente
    if Monter:    ascenseur(+vitesse)    # simulation montée


def lire_entrees():
    global Start, Haut, Bas
    Start = bpA.value()
    Bas   = bpC.value() or (niveau <= -99)    # capteur OU butée simulée
    Haut  = bpB.value() or (niveau >= -1)     # capteur OU butée simulée


def calculer_transitions():
    transitions[0] = g.etapes[0] and Start and (g.tempo[0] > 200)  # T0 : départ
    transitions[1] = g.etapes[1] and Bas                            # T1 : fond atteint
    transitions[2] = g.etapes[2] and Haut                           # T2 : haut atteint


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

while True:
    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    calculer_transitions()
    g.franchir(T, transitions)
    synchro_ms(20)
