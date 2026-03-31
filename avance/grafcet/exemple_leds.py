# =============================================================================
# exemple_leds.py — Généré depuis dessin GRAFCET (grafcet-dessin.jpeg)
# =============================================================================
# GRAFCET à 6 étapes avec divergence ET (séquences parallèles)
# Utilise grafcet_complet.py — version de référence
#
#   Étape 0 — Repos      │ rien
#              BP1        │
#   Étape 1 — Led Bleu   │
#              BP2        │ ← divergence ET (deux branches parallèles)
#   ┌──────────────────────────────────────────────┐
#   Étape 2 — Led Rouge  │      Étape 4 — Led Verte│
#        3 secondes       │           BP3           │
#   Étape 3 — Led Orange │      Étape 5 — (attente)│
#   └──────────────────────────────────────────────┘
#              BP4 (+ étapes 3 ET 5 actives) ← convergence ET
#   Étape 0 — Repos
#
# Toutes les sorties sont en mode CONTINU (1 LED = 1 étape).
# La convergence ET (T4) montre la validation automatique :
#   le moteur vérifie que les étapes 3 ET 5 sont actives.
#
# Fichiers nécessaires sur l'ESP32 :
#   grafcet_complet.py  (moteur GRAFCET)
#   essential.py        (déclarations carte ENIM — sans OLED)
# =============================================================================

from machine import Pin
from grafcet_complet import Grafcet
from essential import synchro_ms, bpA, bpB, bpC, bpD, led_bleue, led_verte, led_jaune, led_rouge


# --- Entrées (carte ENIM) ---
BP1 = bpA    # démarrage                   → broche 25
BP2 = bpB    # lancement séquence parallèle → broche 34
BP3 = bpC    # fin branche droite           → broche 39
BP4 = bpD    # convergence                  → broche 36


# --- Sorties (carte ENIM) ---
Led_Bleu_pin   = led_bleue   # broche 2
Led_Rouge_pin  = led_rouge   # broche 23
Led_Jaune_pin  = led_jaune   # broche 19  ← utilisée pour Led Orange (pas de LED orange)
Led_Verte_pin  = led_verte   # broche 18


# =============================================================================
# GRAFCET
# =============================================================================

g = Grafcet(nb_etapes=6)

T = [
    (0, (0,),   (1,)),      # T0 : BP1              → Repos → Led Bleu
    (1, (1,),   (2, 4)),    # T1 : BP2              → Led Bleu → (Led Rouge ‖ Led Verte)
    (2, (2,),   (3,)),      # T2 : 3 secondes       → Led Rouge → Led Orange
    (3, (4,),   (5,)),      # T3 : BP3              → Led Verte → Attente
    (4, (3, 5), (0,)),      # T4 : BP4 (étapes 3+5) → convergence → Repos
]


# =============================================================================
# VARIABLES
# =============================================================================

Led_Bleu   = False
Led_Rouge  = False
Led_Orange = False   # → led_jaune sur la carte ENIM
Led_Verte  = False

transitions = [False] * len(T)


# =============================================================================
# CYCLE GRAFCET
# =============================================================================

def gerer_actions():
    global Led_Bleu, Led_Rouge, Led_Orange, Led_Verte
    Led_Bleu   = g.etapes[1]   # étape 1 active → allumer bleu
    Led_Rouge  = g.etapes[2]   # étape 2 active → allumer rouge
    Led_Orange = g.etapes[3]   # étape 3 active → allumer orange
    Led_Verte  = g.etapes[4]   # étape 4 active → allumer vert


def affecter_sorties():
    Led_Bleu_pin.value(Led_Bleu)
    Led_Rouge_pin.value(Led_Rouge)
    Led_Jaune_pin.value(Led_Orange)   # led_jaune joue le rôle de Led Orange
    Led_Verte_pin.value(Led_Verte)


def lire_entrees():
    pass   # les boutons sont lus directement dans calculer_transitions


def calculer_transitions():
    # Réceptivités pures — le moteur vérifie les étapes sources (Règle 2)
    # Pour T4 (convergence ET), le moteur vérifie que étapes 3 ET 5 sont actives
    transitions[0] = BP1.value()
    transitions[1] = BP2.value()
    transitions[2] = g.tempo[2] > 3000                # 3 secondes
    transitions[3] = BP3.value()
    transitions[4] = BP4.value()                       # convergence ET (validation auto)


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

print("GRAFCET 6 étapes — divergence/convergence ET")
print("BP1=Start, BP2=Parallèle, BP3=Fin droite, BP4=Convergence")

while True:
    g.franchir(T, transitions)
    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    calculer_transitions()
    synchro_ms(20)
