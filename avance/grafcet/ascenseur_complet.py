# =============================================================================
# ascenseur_complet.py — Exemple de référence GRAFCET complet
# =============================================================================
# Ascenseur simulé sur carte ENIM utilisant TOUTES les fonctionnalités
# du moteur grafcet_complet.py. Cet exemple sert de référence pédagogique
# pour le cours avancé GRAFCET du Fablab.
#
# FONCTIONNALITÉS DÉMONTRÉES :
#
#   ┌─────────────────────────────────────────────────────────────────────┐
#   │ Fonctionnalité              │ Où dans le code                      │
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ Mode CONTINU                │ led_bleue, led_verte, led_jaune,    │
#   │ (1 sortie = 1 étape)       │ moteurs descente/montée             │
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ Mode MÉMORISÉ (SET/RESET)   │ led_rouge clignote 2 Hz             │
#   │ (sortie traverse 2 étapes) │ SET=rising[1], RESET=falling[2]     │
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ Front montant d'entrée (fm) │ bpA=fm[0] (start), bpD=fm[1]       │
#   │                             │ (arrêt d'urgence en front)          │
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ Front montant d'étape       │ g.rising[1] → SET clignoter         │
#   │ (rising)                    │ g.rising[0] → affiche nb de cycles  │
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ Front descendant d'étape    │ g.falling[2] → RESET clignoter      │
#   │ (falling)                   │                                      │
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ Temporisation (tempo)       │ tempo[0] > 500 : anti-rebond au     │
#   │                             │ repos (500 ms avant nouveau départ) │
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ Compteur (nb_cycles)        │ variable Python comptant les        │
#   │                             │ aller-retours. Après 5 → bloqué.    │
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ Compteur d'étape (compt)    │ g.compt[1] compte les appuis bpA    │
#   │                             │ pendant la descente (remis à 0 auto)│
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ Réinitialisation (Règle 6)  │ bpD = arrêt d'urgence →             │
#   │                             │ g.reinitialiser()                    │
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ Validation auto (Règle 2)   │ calculer_transitions() ne contient  │
#   │                             │ que les réceptivités pures           │
#   └─────────────────────────────┴──────────────────────────────────────┘
#
# CORRESPONDANCE CARTE ENIM ↔ ASCENSEUR :
#
#   Entrées :
#     bpA  (Pin 25) → bouton Start (front montant détecté)
#     bpB  (Pin 34) → fin de course HAUT
#     bpC  (Pin 39) → fin de course BAS
#     bpD  (Pin 36) → ARRÊT D'URGENCE → reinitialiser()
#
#   Sorties :
#     led_bleue (Pin  2) → témoin repos                     [CONTINU]
#     led_verte (Pin 18) → commande Descente                [CONTINU]
#     led_jaune (Pin 19) → commande Montée                  [CONTINU]
#     led_rouge (Pin 23) → alarme clignotante 2 Hz          [MÉMORISÉ]
#     np        (Pin 26) → indicateur de niveau NeoPixel
#     Pin 12             → sortie réelle Descente
#     Pin 13             → sortie réelle Montée
#
# GRAFCET (3 étapes) :
#
#       ┌──────────────────────────────────────┐
#       │  ÉTAPE 0 — Repos                     │  led_bleue ON
#       │  nb_cycles++ à chaque retour (rising)│  affiche nb cycles
#       └──────────────────┬───────────────────┘
#                          │ T0 : fm[0] (front montant bpA)
#                          │      ET tempo[0] > 500 ms (anti-rebond)
#                          │      ET pas en maintenance (< 5 cycles)
#       ┌──────────────────▼───────────────────┐
#       │  ÉTAPE 1 — Descente                  │  led_verte ON
#       │  SET clignoter (rising[1])           │  led_rouge clignote
#       │  compt[1]++ si appui bpA (fm[0])     │  (compteur d'étape)
#       └──────────────────┬───────────────────┘
#                          │ T1 : bpC actif OU niveau simulé ≤ -99
#       ┌──────────────────▼───────────────────┐
#       │  ÉTAPE 2 — Montée                    │  led_jaune ON
#       │  RESET clignoter (falling[2])        │  led_rouge clignote
#       └──────────────────┬───────────────────┘  puis s'arrête
#                          │ T2 : bpB actif OU niveau simulé ≥ -1
#                          └────────────────────────────► ÉTAPE 0
#
#   À tout moment : fm[1] (front montant bpD) → reinitialiser()
#
# Fichiers nécessaires sur l'ESP32 :
#   grafcet_complet.py  (moteur GRAFCET)
#   essential.py        (déclarations carte ENIM — sans OLED)
# =============================================================================

from machine import Pin
from time import ticks_ms
from grafcet_complet import Grafcet

from essential import (
    synchro_ms,    # synchronisation cycle 20 ms
    bpA,           # bouton Start          (Pin 25)
    bpB,           # fin de course HAUT    (Pin 34)
    bpC,           # fin de course BAS     (Pin 39)
    bpD,           # ARRÊT D'URGENCE       (Pin 36)
    led_bleue,     # témoin repos          (Pin  2)
    led_verte,     # commande Descente     (Pin 18)
    led_jaune,     # commande Montée       (Pin 19)
    led_rouge,     # alarme clignotante    (Pin 23)
    np,            # NeoPixel 8 LEDs       (Pin 26)
)

# Broches libres pour un vrai moteur (optionnel)
sortie_descente = Pin(12, Pin.OUT)
sortie_montee   = Pin(13, Pin.OUT)

# Sécurité : sorties moteur à 0 au démarrage
sortie_descente.value(0)
sortie_montee.value(0)

# NeoPixel : position initiale de la cabine (en haut = LED 0)
for led in range(8):
    np[led] = (0, 0, 0)
np[0] = (0, 50, 0)
np.write()


# =============================================================================
# INITIALISATION DU MOTEUR GRAFCET
# =============================================================================

# nb_fronts=2 : front montant de bpA (entrée 0) et bpD (entrée 1)
g = Grafcet(nb_etapes=3, nb_fronts=2)

T = [
    (0, (0,), (1,)),   # T0 : Repos → Descente
    (1, (1,), (2,)),   # T1 : Descente → Montée
    (2, (2,), (0,)),   # T2 : Montée → Repos
]


# =============================================================================
# VARIABLES
# =============================================================================

Descendre  = False
Monter     = False
Bas        = False
Haut       = False
clignoter  = False    # mode MÉMORISÉ : led_rouge clignote pendant descente+montée
nb_cycles  = 0        # compteur d'aller-retours (variable Python, pas g.compt)
maintenance = False   # True après 5 cycles → bloque le départ

niveau   = 0      # position simulée : 0 = haut, -100 = bas
vitesse  = 1      # déplacement par cycle
x_ancien = 0      # dernière position NeoPixel affichée

transitions = [False] * len(T)


# =============================================================================
# SIMULATION DU NIVEAU — NeoPixel uniquement
# =============================================================================

def ascenseur(inc):
    global niveau, x_ancien

    niveau = niveau + inc
    if niveau < -100: niveau = -100
    if niveau >    0: niveau =    0

    x = abs(int(-niveau / 12.6))

    if x != x_ancien:
        for led in range(0, x): np[led] = (0, 30, 0)
        for led in range(x, 8): np[led] = (0,  0, 0)
        np[x] = (0, 50, 0)
        np.write()
        x_ancien = x


# =============================================================================
# CYCLE GRAFCET
# =============================================================================

def gerer_actions():
    global Descendre, Monter, clignoter, nb_cycles, maintenance

    # --- Mode CONTINU (1 sortie = 1 étape) ---
    if g.etapes[0]: Descendre = False ; Monter = False
    if g.etapes[1]: Descendre = True  ; Monter = False
    if g.etapes[2]: Descendre = False ; Monter = True

    # --- Mode MÉMORISÉ (SET/RESET — sortie traverse 2 étapes) ---
    # La LED rouge clignote de l'étape 1 (descente) à la fin de l'étape 2 (montée)
    if g.rising[1]:   clignoter = True     # SET : début descente → alarme ON
    if g.falling[2]:  clignoter = False    # RESET : fin montée → alarme OFF

    # --- Compteur d'étape (g.compt) ---
    # g.compt[1] compte les appuis sur bpA PENDANT la descente (étape 1)
    # Il est remis à 0 automatiquement quand l'étape 1 est désactivée.
    # C'est la différence avec nb_cycles (variable Python qui survit entre les étapes).
    if g.etapes[1] and g.fm[0]:
        g.compt[1] += 1
    if g.falling[1]:
        if g.compt[1] > 0:
            print("  Appuis bpA pendant descente :", g.compt[1])

    # --- Compteur d'aller-retours ---
    # nb_cycles s'incrémente à chaque retour au repos (front montant étape 0)
    # On utilise une variable Python (pas g.compt[0]) car g.compt est remis
    # à 0 quand l'étape est désactivée — il ne survit pas entre les cycles.
    # g.compt est fait pour compter des événements DANS une étape active.
    # nb_cycles compte ENTRE les activations successives de l'étape 0.
    if g.rising[0]:
        nb_cycles += 1
        print("Cycle", nb_cycles, "terminé")
        if nb_cycles >= 5:
            maintenance = True
            print(">>> MAINTENANCE : 5 cycles atteints, redémarrage bloqué")


def affecter_sorties():
    # Sorties continues
    led_bleue.value(g.etapes[0])
    led_verte.value(Descendre)
    led_jaune.value(Monter)
    sortie_descente.value(Descendre)
    sortie_montee.value(Monter)
    if Descendre: ascenseur(-vitesse)
    if Monter:    ascenseur(+vitesse)

    # Sortie mémorisée : LED rouge clignote à 2 Hz (250 ms ON / 250 ms OFF)
    if clignoter:
        led_rouge.value(ticks_ms() % 500 < 250)
    else:
        led_rouge.value(0)


def lire_entrees():
    global Bas, Haut

    # Fronts d'entrée : bpA (entrée 0) et bpD (entrée 1)
    # On écrit l'état brut, detecter_fronts_entrees() calcule g.fm[0] et g.fm[1]
    g.entrees[0] = bpA.value()
    g.entrees[1] = bpD.value()

    # Entrées classiques (niveau)
    Bas  = bpC.value() or (niveau <= -99)
    Haut = bpB.value() or (niveau >= -1)


def calculer_transitions():
    # Réceptivités UNIQUEMENT — le moteur vérifie les étapes sources (Règle 2)
    #
    # T0 : front montant de bpA (g.fm[0]) — un appui = un cycle
    #       ET tempo[0] > 500 ms — anti-rebond, empêche le redémarrage trop rapide
    #       ET pas en maintenance — bloque après 5 cycles
    transitions[0] = g.fm[0] and (g.tempo[0] > 500) and not maintenance
    transitions[1] = Bas
    transitions[2] = Haut


# =============================================================================
# BOUCLE PRINCIPALE — cycle GRAFCET normalisé (7 phases)
# =============================================================================

print("Ascenseur GRAFCET complet — bpA=Start, bpD=Arrêt d'urgence")
print("Appuyer sur bpA pour démarrer un cycle")

while True:

    g.franchir(T, transitions)       # 1. évolution + fronts d'étape

    # Arrêt d'urgence : front montant de bpD (g.fm[1])
    # Placé APRÈS franchir() pour que les fronts posés par reinitialiser()
    # soient visibles par gerer_actions() (ils survivent jusqu'au prochain franchir)
    if g.fm[1]:
        g.reinitialiser()
        clignoter = False               # éteindre l'alarme
        nb_cycles = 0                   # remettre le compteur à 0
        maintenance = False             # débloquer
        led_rouge.value(0)              # éteindre la LED rouge immédiatement
        sortie_descente.value(0)        # couper le moteur descente
        sortie_montee.value(0)          # couper le moteur montée
        for led in range(8):            # NeoPixel → position initiale
            np[led] = (0, 0, 0)
        np[0] = (0, 50, 0)
        np.write()
        niveau = 0                      # reset simulation
        x_ancien = 0
        print("!!! ARRÊT D'URGENCE — réinitialisation !!!")

    g.tick(20)                       # 2. timers
    gerer_actions()                  # 3. actions (fronts lisibles ici)
    affecter_sorties()               # 4. sorties physiques
    lire_entrees()                   # 5. capteurs/boutons → g.entrees[i]
    g.detecter_fronts_entrees()      # 6. fronts d'entrée → g.fm[i] / g.fd[i]
    calculer_transitions()           # 7. réceptivités pures
    synchro_ms(20)
