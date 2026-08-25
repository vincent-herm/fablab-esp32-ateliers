# =============================================================================
# grafcet_7.py — Exercice 7
# =============================================================================
# GRAFCET 4 étapes sur carte Vincent.
#
# GRAFCET :
#
#   Étape 0 — Veille
#     [C] NeoPixel éteint, LED rouge off, LED verte off
#       │ T0 : fm[0] (bpA) OU fm[1] (bpB)
#   Étape 1 — Aller (gauche → droite, bleu, 1 seconde)
#     [C] 1 LED bleue se déplace de 0 à 7 (125 ms / LED)
#       │ T1 : tempo[1] >= 1000 ms
#   Étape 2 — Attente à droite
#     [C] LED 7 bleue fixe
#       │ T2 : bpC ET bpD simultanément (niveau)
#   Étape 3 — Retour (droite → gauche, rouge, 1 seconde)
#     [C] 1 LED rouge se déplace de 7 à 0 (125 ms / LED)
#     [M] tp1 (fm[2]) → toggle clignotement LED rouge
#     [M] tp2 (fm[3]) → toggle état LED verte
#       │ T3 : tempo[3] >= 1000 ms → retour Étape 0
#
# ENTRÉES :
#   bpA  (Pin 25) → start                         (front montant fm[0])
#   bpB  (Pin 34) → start (idem bpA)              (front montant fm[1])
#   bpC  (Pin 39) → départ retour (avec bpD)      (niveau)
#   bpD  (Pin 36) → départ retour (avec bpC)      (niveau)
#   tp1  (Pin 15) → toggle cligno LED rouge        (front montant fm[2])
#   tp2  (Pin  4) → toggle LED verte               (front montant fm[3])
#
# SORTIES :
#   NeoPixel  (Pin 26) → chenillard bleu (aller) / rouge (retour)
#   led_rouge (Pin 23) → clignote 2 Hz si activée  [M]
#   led_verte (Pin 18) → suit l'état toggleé       [M]
#
# Fichiers nécessaires : grafcet_complet.py, essential.py
# =============================================================================

from time import ticks_ms
from grafcet_complet import Grafcet
from essential import synchro_ms, bpA, bpB, bpC, bpD, tp1, tp2, led_rouge, led_verte, np

# =============================================================================
# GRAFCET — 4 étapes
# =============================================================================

# nb_fronts=4 : bpA(0), bpB(1), tp1(2), tp2(3)
g = Grafcet(nb_etapes=4, nb_fronts=4)

T = [
    (0, (0,), (1,)),   # T0 : Veille → Aller       (bpA ou bpB)
    (1, (1,), (2,)),   # T1 : Aller → Attente       (1 seconde)
    (2, (2,), (3,)),   # T2 : Attente → Retour      (bpC ET bpD simultanés)
    (3, (3,), (0,)),   # T3 : Retour → Veille       (1 seconde)
]

transitions = [False] * 4

# =============================================================================
# VARIABLES MÉMORISÉES
# =============================================================================

clignoter_rouge = False   # [M] toggle sur fm tp1 (actif pendant É3)
led_verte_etat  = False   # [M] toggle sur fm tp2 (actif pendant É3)

# NeoPixel éteint au démarrage
for i in range(8):
    np[i] = (0, 0, 0)
np.write()


# =============================================================================
# CYCLE GRAFCET
# =============================================================================

def gerer_actions():
    global clignoter_rouge, led_verte_etat

    # --- É0 : NeoPixel éteint au retour en veille ---
    if g.rising[0]:
        for i in range(8):
            np[i] = (0, 0, 0)
        np.write()
        # led_rouge et led_verte conservent leur état (parallélisme indépendant)

    # --- É1 : aller gauche→droite, bleu [C] ---
    if g.etapes[1]:
        pos = min(g.tempo[1] // 125, 7)
        for i in range(8):
            np[i] = (0, 0, 40) if i == pos else (0, 0, 0)
        np.write()

    # --- É2 : attente à droite — LED 7 bleue fixe [C] ---
    if g.rising[2]:
        for i in range(8):
            np[i] = (0, 0, 0)
        np[7] = (0, 0, 40)
        np.write()

    # --- É3 : retour droite→gauche, rouge [C] ---
    if g.etapes[3]:
        pos = 7 - min(g.tempo[3] // 125, 7)
        for i in range(8):
            np[i] = (40, 0, 0) if i == pos else (0, 0, 0)
        np.write()

    # --- tp1 → toggle clignotement LED rouge [M] — TOUJOURS actif ---
    if g.fm[2]:
        clignoter_rouge = not clignoter_rouge

    # --- tp2 → toggle LED verte [M] — TOUJOURS actif ---
    if g.fm[3]:
        led_verte_etat = not led_verte_etat


def affecter_sorties():
    # LED rouge : clignotement 2 Hz si activée [M]
    if clignoter_rouge:
        led_rouge.value(ticks_ms() % 500 < 250)
    else:
        led_rouge.value(0)

    # LED verte : suit l'état mémorisé [M]
    led_verte.value(led_verte_etat)


def lire_entrees():
    g.entrees[0] = bpA.value()          # bpA
    g.entrees[1] = bpB.value()          # bpB
    g.entrees[2] = tp1.read() < 150     # tp1 touché (repos ~260, touché ~50)
    g.entrees[3] = tp2.read() < 150     # tp2 touché (repos ~270, touché ~60)


def calculer_transitions():
    transitions[0] = g.fm[0] or g.fm[1]           # bpA OU bpB (front)
    transitions[1] = g.tempo[1] >= 1000            # 1 seconde écoulée
    transitions[2] = bpC.value() and bpD.value()   # bpC ET bpD simultanés
    transitions[3] = g.tempo[3] >= 1000            # 1 seconde écoulée


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

print("=== Grafcet 7 ===")
print("bpA ou bpB = start")
print("bpC + bpD  = départ retour")
print("tp1 = toggle cligno rouge   tp2 = toggle LED verte")

while True:
    g.franchir(T, transitions)
    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    g.detecter_fronts_entrees()
    calculer_transitions()
    synchro_ms(20)
