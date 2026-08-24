# =============================================================================
# chenillard_bidir.py — Chenillard NeoPixel bidirectionnel avec TouchPads
# =============================================================================
# GRAFCET 4 étapes sur carte ENIM.
#
# GRAFCET :
#
#   Étape 0 — Veille
#     [C] NeoPixel éteint
#       │ T0 : fm[0]  (toucher tp1)
#   Étape 1 — Aller  (gauche → droite, bleu)
#     [C] 1 LED bleue se déplace de 0 à 7 (VITESSE ms par LED)
#       │ T1 : tempo[1] >= 8 * VITESSE  (LED 7 atteinte et affichée)
#   Étape 2 — Attente à droite
#     [C] LED 7 bleue fixe
#     (tp2 ignoré pendant É1 — il n'est actif qu'ici)
#       │ T2 : fm[1]  (toucher tp2)
#   Étape 3 — Retour  (droite → gauche, rouge)
#     [C] 1 LED rouge se déplace de 7 à 0 (VITESSE ms par LED)
#       │ T3 : tempo[3] >= 8 * VITESSE  (LED 0 atteinte et affichée)
#       → retour Étape 0
#
#   À tout moment : bpA → reinitialiser() + NeoPixel éteint
#
# ENTRÉES :
#   tp1  (Pin 15) → déclenche l'aller      (front montant fm[0])
#   tp2  (Pin  4) → déclenche le retour    (front montant fm[1])
#   bpA  (Pin 25) → arrêt d'urgence        (niveau)
#
# SORTIES :
#   NeoPixel (Pin 26) → 8 LEDs RGB
#
# Fichiers nécessaires sur l'ESP32 : grafcet_complet.py, essential.py
# =============================================================================

from grafcet_complet import Grafcet
from essential import synchro_ms, bpA, tp1, tp2, np

VITESSE = 200   # millisecondes par LED (200 ms = animation sur 1.6 s)

# =============================================================================
# GRAFCET — 4 étapes
# =============================================================================

# nb_fronts=2 : tp1(0), tp2(1)
g = Grafcet(nb_etapes=4, nb_fronts=2)

T = [
    (0, (0,), (1,)),   # T0 : Veille → Aller      (front tp1)
    (1, (1,), (2,)),   # T1 : Aller → Attente      (arrivé à droite)
    (2, (2,), (3,)),   # T2 : Attente → Retour     (front tp2)
    (3, (3,), (0,)),   # T3 : Retour → Veille      (arrivé à gauche)
]

transitions = [False] * 4

# NeoPixel éteint au démarrage
for i in range(8):
    np[i] = (0, 0, 0)
np.write()


# =============================================================================
# CYCLE GRAFCET
# =============================================================================

def gerer_actions():

    # É0 — Veille : tout éteindre au retour [C]
    if g.rising[0]:
        for i in range(8):
            np[i] = (0, 0, 0)
        np.write()

    # É1 — Aller : 1 LED bleue se déplace de 0 à 7 [C]
    if g.etapes[1]:
        pos = min(g.tempo[1] // VITESSE, 7)
        for i in range(8):
            np[i] = (0, 0, 40) if i == pos else (0, 0, 0)
        np.write()

    # É2 — Attente à droite : LED 7 bleue fixe [C]
    if g.rising[2]:
        for i in range(8):
            np[i] = (0, 0, 0)
        np[7] = (0, 0, 40)
        np.write()

    # É3 — Retour : 1 LED rouge se déplace de 7 à 0 [C]
    if g.etapes[3]:
        pos = 7 - min(g.tempo[3] // VITESSE, 7)
        for i in range(8):
            np[i] = (40, 0, 0) if i == pos else (0, 0, 0)
        np.write()


def affecter_sorties():
    pass


def lire_entrees():
    g.entrees[0] = tp1.read() < 350   # tp1 touché
    g.entrees[1] = tp2.read() < 350   # tp2 touché


def calculer_transitions():
    transitions[0] = g.fm[0]                       # front montant tp1
    transitions[1] = g.tempo[1] >= 8 * VITESSE     # LED 7 atteinte et affichée
    transitions[2] = g.fm[1]                       # front montant tp2
    transitions[3] = g.tempo[3] >= 8 * VITESSE     # LED 0 atteinte et affichée


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

print("=== Chenillard bidirectionnel ===")
print("tp1 = aller (bleu)   tp2 = retour (rouge)   bpA = arrêt")

while True:

    g.franchir(T, transitions)

    # Arrêt d'urgence — bpA remet tout à zéro
    if bpA.value():
        g.reinitialiser()
        for i in range(8):
            np[i] = (0, 0, 0)
        np.write()
        print("Arrêt")

    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    g.detecter_fronts_entrees()
    calculer_transitions()
    synchro_ms(20)
