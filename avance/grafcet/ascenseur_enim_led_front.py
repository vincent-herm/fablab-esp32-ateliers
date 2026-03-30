# =============================================================================
# ascenseur_enim_led_front.py — Ascenseur avec détection de front montant
# =============================================================================
# Même ascenseur que ascenseur_enim_led.py, mais le bouton Start (bpA)
# est traité en FRONT MONTANT au lieu d'un simple niveau logique.
#
# POURQUOI ?
#   Sans front : si on maintient bpA enfoncé, l'ascenseur redémarre
#   automatiquement à chaque retour en étape 0 (la condition reste vraie).
#   Avec front : il faut RELÂCHER puis RE-APPUYER pour relancer un cycle.
#   Seul l'instant précis de l'appui déclenche la transition.
#
# PRINCIPE :
#   Niveau   = lire l'état du bouton (True tant qu'il est enfoncé)
#   Front    = détecter le CHANGEMENT d'état (True pendant 1 seul cycle)
#
#   fm[i] = front montant  : bouton relâché → enfoncé (1 cycle)
#   fd[i] = front descendant : bouton enfoncé → relâché (1 cycle)
#
# CE QUI CHANGE PAR RAPPORT À ascenseur_enim_led.py :
#   1. Grafcet(..., nb_fronts=1)         → réserve 1 front à surveiller
#   2. g.entrees[0] = bpA.value()        → on écrit l'état brut dans lire_entrees()
#   3. g.detecter_fronts_entrees()       → on appelle dans la boucle (phase 6)
#   4. g.fm[0] dans calculer_transitions → on utilise le front au lieu du niveau
#      (remplace : Start and tempo[0] > 200)
#
# CORRESPONDANCE CARTE ENIM ↔ ASCENSEUR :
#
#   Entrées :
#     bpA  (Pin 25) → bouton Start (front montant détecté)
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
#                          │ T0 : front montant de bpA (↑)
#       ┌──────────────────▼───────────────────┐
#       │  ÉTAPE 1 — Descente                  │  led_verte allumée
#       └──────────────────┬───────────────────┘
#                          │ T1 : bpC actif OU niveau simulé ≤ -99
#       ┌──────────────────▼───────────────────┐
#       │  ÉTAPE 2 — Montée                    │  led_jaune allumée
#       └──────────────────┬───────────────────┘
#                          │ T2 : bpB actif OU niveau simulé ≥ -1
#                          └────────────────────────────► ÉTAPE 0
#
# Fichiers nécessaires sur l'ESP32 :
#   grafcet.py    (moteur GRAFCET)
#   essential.py  (déclarations carte ENIM — sans OLED)
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

# NeoPixel : position initiale de la cabine (en haut = LED 0)
for led in range(8):
    np[led] = (0, 0, 0)
np[0] = (0, 50, 0)    # cabine en position haute
np.write()


# =============================================================================
# INITIALISATION DU MOTEUR GRAFCET
# =============================================================================

# nb_fronts=1 : on surveille le front montant de bpA (entrée 0)
g = Grafcet(nb_etapes=3, nb_fronts=1, etape_initiale=0)

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
    global Haut, Bas
    g.entrees[0] = bpA.value()                    # état brut du bouton Start
    Bas   = bpC.value() or (niveau <= -99)        # capteur OU butée simulée
    Haut  = bpB.value() or (niveau >= -1)         # capteur OU butée simulée


def calculer_transitions():
    # T0 : g.fm[0] = front montant de bpA → True uniquement à l'APPUI
    #       (même si on maintient le bouton, ça ne redémarre pas)
    transitions[0] = g.etapes[0] and g.fm[0]
    transitions[1] = g.etapes[1] and Bas                            # T1 : fond atteint
    transitions[2] = g.etapes[2] and Haut                           # T2 : haut atteint


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

while True:
    g.franchir(T, transitions)
    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    g.detecter_fronts_entrees()      # détecte fm[0] / fd[0] de bpA
    calculer_transitions()
    synchro_ms(20)
