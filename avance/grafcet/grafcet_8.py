# =============================================================================
# grafcet_8.py — Divergence ET / Convergence ET
# =============================================================================
# GRAFCET 7 étapes sur carte ENIM.
#
# GRAFCET :
#
#   Étape 0 — Veille
#     [C] NeoPixel éteint, LEDs off
#       │ T0 : fm[0] (bpA) → DIVERGENCE ET
#       ├─────────────────────────────────────────────┐
#   Branch G                                     Branch D
#   Étape 1 — Arc-en-ciel                        Étape 4 — Attente bpC
#     [C] NeoPixel arc-en-ciel                     (rien)
#       │ T1 : tempo >= 3000 ms                      │ T4 : fm[2] (bpC)
#   Étape 2 — Attente bpB                        Étape 5 — Cligno orange
#     [C] NeoPixel éteint                          [C] LED jaune clignote 2 Hz
#       │ T2 : fm[1] (bpB)                           │ T5 : fm[2] (bpC)
#   Étape 3 — LED bleue fixe                     Étape 6 — Fin branch D
#     [C] led_bleue ON                             [C] LED jaune OFF
#     (attente convergence ET)                     (attente convergence ET)
#       └──────────── T6 : CONVERGENCE ET ───────────┘
#                          (É3 ET É6 actives)
#                               │
#                          retour Étape 0
#
# ENTRÉES :
#   bpA  (Pin 25) → démarre les deux branches     (front montant fm[0])
#   bpB  (Pin 34) → allume LED bleue (branch G)   (front montant fm[1])
#   bpC  (Pin 39) → 1er appui: start orange       (front montant fm[2])
#                   2e appui : stop orange
#
# SORTIES :
#   NeoPixel  (Pin 26) → arc-en-ciel en É1        [C]
#   led_bleue (Pin  2) → allumée en É3            [C]
#   led_jaune (Pin 19) → clignote 2 Hz en É5      [C]
#
# Note : bpC utilise fm[2] pour T4 ET T5. Le moteur sait quelle
#        transition franchir selon l'étape active (É4 ou É5).
#
# Fichiers nécessaires : grafcet_complet.py, essential.py
# =============================================================================

from time import ticks_ms
from grafcet_complet import Grafcet
from essential import synchro_ms, bpA, bpB, bpC, led_bleue, led_jaune, np


# =============================================================================
# ARC-EN-CIEL
# =============================================================================

def arc_en_ciel(h):
    """Convertit une teinte (0-255) en triplet RGB (luminosité réduite)."""
    h = h % 256
    B = 35
    if h < 85:
        return (B - h * B // 85, h * B // 85, 0)
    elif h < 170:
        h -= 85
        return (0, B - h * B // 85, h * B // 85)
    else:
        h -= 170
        return (h * B // 85, 0, B - h * B // 85)


# =============================================================================
# GRAFCET — 7 étapes
# =============================================================================

# nb_fronts=3 : bpA(0), bpB(1), bpC(2)
g = Grafcet(nb_etapes=7, nb_fronts=3)

T = [
    (0, (0,),    (1, 4)),  # T0 : bpA → DIVERGENCE ET (branch G + branch D)
    (1, (1,),    (2,)),    # T1 : arc-en-ciel terminé (3 s)
    (2, (2,),    (3,)),    # T2 : bpB → LED bleue ON
    (3, (4,),    (5,)),    # T3 : bpC (1er) → start cligno orange
    (4, (5,),    (6,)),    # T4 : bpC (2e)  → stop cligno orange
    (5, (3, 6),  (0,)),    # T5 : CONVERGENCE ET → retour veille
]

transitions = [False] * 6

# NeoPixel éteint au démarrage
for i in range(8):
    np[i] = (0, 0, 0)
np.write()


# =============================================================================
# CYCLE GRAFCET
# =============================================================================

def gerer_actions():

    # --- É0 : tout éteindre au retour [C] ---
    if g.rising[0]:
        for i in range(8):
            np[i] = (0, 0, 0)
        np.write()

    # --- É1 : arc-en-ciel NeoPixel [C] ---
    if g.etapes[1]:
        hue = (g.tempo[1] // 12) % 256      # cycle complet en ~3 s
        for i in range(8):
            np[i] = arc_en_ciel((hue + i * 32) % 256)
        np.write()

    # --- É2 : NeoPixel éteint (attente bpB) [C] ---
    if g.rising[2]:
        for i in range(8):
            np[i] = (0, 0, 0)
        np.write()


def affecter_sorties():

    # LED bleue : allumée uniquement en É3 [C]
    led_bleue.value(g.etapes[3])

    # LED jaune : clignote 2 Hz en É5, éteinte sinon [C]
    if g.etapes[5]:
        led_jaune.value(ticks_ms() % 500 < 250)
    else:
        led_jaune.value(0)


def lire_entrees():
    g.entrees[0] = bpA.value()
    g.entrees[1] = bpB.value()
    g.entrees[2] = bpC.value()


def calculer_transitions():
    transitions[0] = g.fm[0]               # bpA → divergence ET
    transitions[1] = g.tempo[1] >= 3000    # 3 secondes arc-en-ciel
    transitions[2] = g.fm[1]               # bpB → LED bleue
    transitions[3] = g.fm[2]               # bpC (1er appui) → start orange
    transitions[4] = g.fm[2]               # bpC (2e appui)  → stop orange
    transitions[5] = True                   # convergence ET (validation auto)


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

print("=== Grafcet 8 — Divergence ET / Convergence ET ===")
print("bpA = démarrer les deux branches")
print("bpB = allumer LED bleue (branch G)")
print("bpC = 1er appui: cligno orange  2e appui: stop (branch D)")
print("Les deux branches se rejoignent automatiquement quand les deux sont finies")

while True:
    g.franchir(T, transitions)
    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    g.detecter_fronts_entrees()
    calculer_transitions()
    synchro_ms(20)
