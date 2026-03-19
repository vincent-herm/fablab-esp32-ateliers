# =============================================================================
# ascenseur_enim.py — Simulation d'ascenseur sur carte d'expérimentation ENIM
# =============================================================================
# Adaptation de ascenseur.py pour la carte ESP32 ENIM.
#
# PRINCIPE D'INTÉGRATION :
#   grafcet.py   → moteur pur, aucune dépendance matérielle (ne jamais modifier)
#   essential.py → déclarations matérielles de la carte ENIM (ne jamais modifier)
#   ce fichier   → fait le lien entre les deux : importe sélectivement ce qu'il
#                  utilise depuis essential, et confie la logique à grafcet.py
#
# CORRESPONDANCE CARTE ENIM ↔ ASCENSEUR :
#
#   Entrées physiques (capteurs / boutons) :
#     bpA  (Pin 25) → bouton Start       (lancer le cycle)
#     bpB  (Pin 34) → fin de course HAUT (cabine en position haute)
#     bpC  (Pin 39) → fin de course BAS  (cabine en position basse)
#
#   Sorties physiques (actionneurs simulés par les LEDs de la carte) :
#     led_verte (Pin 18) → commande Descente  (s'allume quand la cabine descend)
#     led_jaune (Pin 19) → commande Montée    (s'allume quand la cabine monte)
#     led_bleue (Pin  2) → LED témoin         (allumée à l'étape 0 = repos)
#
#   Affichage :
#     np      (Pin 26, 8 LEDs) → indicateur de niveau (barre de progression)
#     display (SH1106, I2C)   → affichage numérique du niveau sur OLED
#
#   Sorties libres (connecteurs 12 et 13 pour brancher un vrai moteur) :
#     Pin 12 → commande réelle Descente (optionnel, si relais ou driver moteur)
#     Pin 13 → commande réelle Montée   (optionnel, si relais ou driver moteur)
#
# GRAFCET DE L'ASCENSEUR (3 étapes) :
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

from machine import Pin              # accès aux broches GPIO de l'ESP32
from grafcet  import Grafcet         # moteur GRAFCET (grafcet.py dans le même dossier)

# --- Imports sélectifs depuis essential.py ---
# On n'importe QUE ce dont cet programme a besoin.
# Cela évite d'initialiser tout le matériel de la carte inutilement.
from essential import (
    synchro_ms,    # synchronisation du cycle à 20 ms (non-bloquant)
    bpA,           # bouton poussoir A  → Start         (Pin 25)
    bpB,           # bouton poussoir B  → fin de course HAUT (Pin 34)
    bpC,           # bouton poussoir C  → fin de course BAS  (Pin 39)
    led_bleue,     # LED bleue          → témoin étape 0     (Pin  2)
    led_verte,     # LED verte          → commande Descente  (Pin 18)
    led_jaune,     # LED jaune          → commande Montée    (Pin 19)
    np,            # bandeau NeoPixel   → indicateur niveau  (Pin 26, 8 LEDs)
    display,       # écran OLED SH1106  → affichage numérique
)

# --- Broches libres pour un vrai moteur (optionnel) ---
# Ces broches (12 et 13) sont libres sur la carte ENIM.
# Les connecter à un driver moteur ou un relais pour une application réelle.
sortie_descente = Pin(12, Pin.OUT)   # commande réelle Descente
sortie_montee   = Pin(13, Pin.OUT)   # commande réelle Montée

# Éteindre les sorties moteur au démarrage (sécurité)
sortie_descente.value(0)
sortie_montee.value(0)

# Éteindre le bandeau NeoPixel au démarrage
for led in range(8):
    np[led] = (0, 0, 0)    # couleur noire = éteinte
np.write()                  # envoyer la commande au bandeau


# =============================================================================
# INITIALISATION DU MOTEUR GRAFCET
# =============================================================================

g = Grafcet(nb_etapes=3, etape_initiale=0)
# g.etapes = [True, False, False] → seule l'étape 0 est active au démarrage


# =============================================================================
# TABLE DE TRANSITIONS
# Format : (indice_transition, (étapes_à_désactiver,), (étapes_à_activer,))
# =============================================================================

T = [
    (0, (0,), (1,)),   # T0 : étape 0 → étape 1  (Repos → Descente)
    (1, (1,), (2,)),   # T1 : étape 1 → étape 2  (Descente → Montée)
    (2, (2,), (0,)),   # T2 : étape 2 → étape 0  (Montée → Repos)
]


# =============================================================================
# VARIABLES DE L'APPLICATION
# =============================================================================

# Actions (calculées dans gerer_actions, appliquées dans affecter_sorties)
Descendre = False    # True → cabine en train de descendre
Monter    = False    # True → cabine en train de monter

# Entrées (lues dans lire_entrees)
Start = False    # True quand bpA est pressé
Haut  = False    # True quand bpB actif OU niveau simulé atteint le plafond
Bas   = False    # True quand bpC actif OU niveau simulé atteint le plancher

# Simulation physique de la cabine
niveau          = 0    # position simulée : 0 = haut, -100 = bas
vitesse         = 1    # déplacement par cycle (augmenter pour accélérer)
x_ancien        = 0    # dernière position affichée sur le NeoPixel
compt_affichage = 0    # compteur pour limiter le rafraîchissement OLED

# Tableau des réceptivités (une entrée par transition dans T)
transitions = [False] * len(T)


# =============================================================================
# FONCTION : simulation et affichage du niveau de la cabine
# =============================================================================

def ascenseur(inc):
    """
    Met à jour le niveau simulé et rafraîchit le NeoPixel et l'OLED.
    :param inc: incrément de déplacement (+vitesse = montée, -vitesse = descente)
    """
    global niveau, x_ancien, compt_affichage

    # Déplacement et butées
    niveau = niveau + inc
    if niveau < -100: niveau = -100    # plancher
    if niveau >    0: niveau =    0    # plafond

    # Calcul de la position sur le NeoPixel (0 = haut, 7 = bas)
    x = abs(int(-niveau / 12.6))

    # Mise à jour du NeoPixel uniquement si la position a changé
    if x != x_ancien:
        for led in range(0, x): np[led] = (0, 30, 0)    # LEDs sous la cabine : vert
        for led in range(x, 8): np[led] = (0,  0, 0)    # LEDs au-dessus : éteintes
        np[x] = (0, 50, 0)                               # position exacte : vert vif
        np.write()
        x_ancien = x

    # Rafraîchissement OLED tous les 3 cycles (allège le bus I2C)
    compt_affichage += 1
    if compt_affichage == 3:
        display.fill_rect(60, 0, 60, 64, 0)                       # efface la zone
        display.fill_rect(60, 0, 10, -int(niveau / 2), 1)         # dessine la barre
        display.show()
        compt_affichage = 0


# =============================================================================
# PHASE 1 — GÉRER LES ACTIONS
# Calcule les variables logiques selon les étapes actives.
# Aucune sortie physique ici — uniquement des variables booléennes.
# =============================================================================

def gerer_actions():
    global Descendre, Monter

    if g.etapes[0]:
        Descendre = False    # étape Repos : arrêt complet
        Monter    = False

    if g.etapes[1]:
        Descendre = True     # étape Descente : commande descente active
        Monter    = False

    if g.etapes[2]:
        Descendre = False    # étape Montée : commande montée active
        Monter    = True


# =============================================================================
# PHASE 2 — AFFECTER LES SORTIES
# Applique les variables logiques sur le matériel de la carte ENIM.
# =============================================================================

def affecter_sorties():

    # --- LEDs de la carte ENIM (simulation visuelle) ---
    led_bleue.value(g.etapes[0])    # bleue allumée = repos
    led_verte.value(Descendre)      # verte allumée = descente en cours
    led_jaune.value(Monter)         # jaune allumée = montée en cours

    # --- Sorties réelles (broches libres 12 et 13 pour driver moteur) ---
    sortie_descente.value(Descendre)    # commande réelle moteur Descente
    sortie_montee.value(Monter)         # commande réelle moteur Montée

    # --- Simulation du mouvement sur NeoPixel et OLED ---
    if Descendre: ascenseur(-vitesse)    # descend d'un cran
    if Monter:    ascenseur(+vitesse)    # monte d'un cran


# =============================================================================
# PHASE 3 — LIRE LES ENTRÉES
# Lit les boutons de la carte ENIM et met à jour les variables logiques.
# =============================================================================

def lire_entrees():
    global Start, Haut, Bas

    Start = bpA.value()                           # bouton A → Start

    # Fin de course BAS : bouton C OU simulation au plancher
    Bas   = bpC.value() or (niveau <= -99)

    # Fin de course HAUT : bouton B OU simulation au plafond
    Haut  = bpB.value() or (niveau >= -1)


# =============================================================================
# PHASE 4 — CALCULER LES TRANSITIONS
# Évalue les réceptivités de chaque transition.
# =============================================================================

def calculer_transitions():

    # T0 : Start pressé ET délai anti-rebond de 200 ms écoulé
    transitions[0] = g.etapes[0] and Start and (g.tempo[0] > 200)

    # T1 : fin de course basse atteinte
    transitions[1] = g.etapes[1] and Bas

    # T2 : fin de course haute atteinte
    transitions[2] = g.etapes[2] and Haut


# =============================================================================
# BOUCLE PRINCIPALE — cycle GRAFCET normalisé (20 ms)
# =============================================================================

while True:

    g.tick(20)                       # 1. Mise à jour des timers

    gerer_actions()                  # 2. Calcul des actions

    affecter_sorties()               # 3. Application sur le matériel

    lire_entrees()                   # 4. Lecture des entrées

    calculer_transitions()           # 5. Évaluation des réceptivités

    g.franchir(T, transitions)       # 6. Franchissement des transitions

    synchro_ms(20)                   # 7. Synchronisation cycle 20 ms
