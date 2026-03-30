# =============================================================================
# ascenseur_enim_v2.py — Ascenseur ENIM avec affichage NeoPixel progressif
# =============================================================================
# Version 2 : utilise NeoProgressif pour un affichage fluide du niveau.
#
# Fichiers nécessaires sur l'ESP32 :
#   grafcet.py    (moteur GRAFCET)
#   neoprog.py    (affichage NeoPixel progressif)
#   essential.py  (déclarations carte ENIM — sans OLED)
#
# GRAFCET (inchangé) :
#   Étape 0 — Repos     │ T0 : bpA ET tempo[0] > 200 ms
#   Étape 1 — Descente  │ T1 : bpC OU niveau ≤ -99
#   Étape 2 — Montée    │ T2 : bpB OU niveau ≥ -1
# =============================================================================

from machine  import Pin
from grafcet  import Grafcet
from neoprog  import NeoProgressif      # ← nouveau : affichage fluide

from essential import (
    synchro_ms,
    bpA, bpB, bpC,
    led_bleue, led_verte, led_jaune,
)

# --- NeoProgressif sur Pin 26, 8 LEDs, couleur verte ---
# On ne récupère plus np depuis essential : NeoProgressif crée son propre NeoPixel
neo = NeoProgressif(pin=26, n=8, couleur=(0, 255, 0))

# --- Broches moteur sur les connecteurs libres ---
sortie_descente = Pin(12, Pin.OUT)
sortie_montee   = Pin(13, Pin.OUT)
sortie_descente.value(0)
sortie_montee.value(0)


# =============================================================================
# GRAFCET
# =============================================================================

g = Grafcet(nb_etapes=3, etape_initiale=0)

T = [
    (0, (0,), (1,)),   # Repos → Descente
    (1, (1,), (2,)),   # Descente → Montée
    (2, (2,), (0,)),   # Montée → Repos
]

# =============================================================================
# VARIABLES
# =============================================================================

Descendre = False
Monter    = False
Start     = False
Haut      = False
Bas       = False

niveau  = 0      # position simulée : 0 = haut, -100 = bas
vitesse = 1      # déplacement par cycle

transitions = [False] * len(T)


# =============================================================================
# SIMULATION DU NIVEAU — NeoProgressif
# =============================================================================

def ascenseur(inc):
    """
    Déplace la cabine simulée et met à jour le NeoPixel progressivement.
    :param inc: -vitesse = descente, +vitesse = montée
    """
    global niveau

    niveau = niveau + inc
    if niveau < -100: niveau = -100
    if niveau >    0: niveau =    0

    # Conversion niveau [-100, 0] → valeur [1000, 0] pour NeoProgressif
    # niveau=0   → x=0    (bandeau éteint, cabine en haut)
    # niveau=-100 → x=1000 (bandeau plein, cabine en bas)
    neo.afficher(int(-niveau * 10))


# =============================================================================
# CYCLE GRAFCET
# =============================================================================

def gerer_actions():
    global Descendre, Monter
    if g.etapes[0]: Descendre = False ; Monter = False
    if g.etapes[1]: Descendre = True  ; Monter = False
    if g.etapes[2]: Descendre = False ; Monter = True


def affecter_sorties():
    led_bleue.value(g.etapes[0])
    led_verte.value(Descendre)
    led_jaune.value(Monter)
    sortie_descente.value(Descendre)
    sortie_montee.value(Monter)
    if Descendre: ascenseur(-vitesse)
    if Monter:    ascenseur(+vitesse)


def lire_entrees():
    global Start, Haut, Bas
    Start = bpA.value()
    Bas   = bpC.value() or (niveau <= -99)
    Haut  = bpB.value() or (niveau >= -1)


def calculer_transitions():
    transitions[0] = g.etapes[0] and Start and (g.tempo[0] > 200)
    transitions[1] = g.etapes[1] and Bas
    transitions[2] = g.etapes[2] and Haut


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

while True:
    g.franchir(T, transitions)
    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    calculer_transitions()
    synchro_ms(20)
