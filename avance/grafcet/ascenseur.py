# =============================================================================
# ascenseur.py — Simulation d'ascenseur avec moteur GRAFCET
# =============================================================================
# Démontre l'utilisation de la classe Grafcet sur un exemple concret.
#
# GRAFCET DE L'ASCENSEUR (3 étapes) :
#
#       ┌──────────────────────────────────┐
#       │  ÉTAPE 0 — Repos                 │  Actions : Descendre=0, Monter=0
#       └────────────────┬─────────────────┘
#                        │ T0 : Start ET tempo[0] > 200 ms
#       ┌────────────────▼─────────────────┐
#       │  ÉTAPE 1 — Descente              │  Actions : Descendre=1, Monter=0
#       └────────────────┬─────────────────┘
#                        │ T1 : Bas (fin de course basse atteinte)
#       ┌────────────────▼─────────────────┐
#       │  ÉTAPE 2 — Montée                │  Actions : Descendre=0, Monter=1
#       └────────────────┬─────────────────┘
#                        │ T2 : Haut (fin de course haute atteinte)
#                        └──────────────────────────────► ÉTAPE 0
#
# CÂBLAGE :
#   Pin 25 (IN)  → bouton Start
#   Pin 34 (IN)  → capteur fin de course HAUT
#   Pin 39 (IN)  → capteur fin de course BAS
#   Pin 18 (OUT) → sortie Descente (moteur / actionneur)
#   Pin 19 (OUT) → sortie Montée  (moteur / actionneur)
#   Pin  2 (OUT) → LED témoin (allumée à l'étape 0 = repos)
#   Pin 13       → bandeau NeoPixel 8 LEDs (indicateur de niveau)
#   Pin 22/21    → I2C SCK/SDA → écran OLED SH1106 128×64
# =============================================================================

from machine import Pin, I2C       # accès aux broches et au bus I2C de l'ESP32
from time    import sleep           # pause bloquante (utilisée à l'init si besoin)
import neopixel                     # pilotage des LEDs WS2812 (NeoPixel)

from essential import synchro_ms   # synchronisation de la boucle principale (non-bloquant)
from grafcet  import Grafcet        # moteur GRAFCET (fichier grafcet.py dans le même dossier)

# --- Écran OLED SH1106 ---
from sh1106 import SH1106_I2C                              # driver MicroPython pour SH1106
i2c     = I2C(scl=Pin(22), sda=Pin(21), freq=400000)       # bus I2C : SCK=22, SDA=21, vitesse 400 kHz
display = SH1106_I2C(128, 64, i2c, Pin(16), 0x3c)          # 128×64 pixels, reset Pin16, adresse I2C 0x3C
display.sleep(False)                                        # sortir du mode veille (activer l'écran)


# =============================================================================
# DÉCLARATION DES ENTRÉES (capteurs et boutons)
# =============================================================================

pStart = Pin(25, Pin.IN)    # bouton poussoir Start  — appui → lancement du cycle
pHaut  = Pin(34, Pin.IN)    # fin de course HAUT     — actif quand la cabine est en haut
pBas   = Pin(39, Pin.IN)    # fin de course BAS      — actif quand la cabine est en bas


# =============================================================================
# DÉCLARATION DES SORTIES (actionneurs)
# =============================================================================

pDescente = Pin(18, Pin.OUT)   # commande moteur descente
pMontee   = Pin(19, Pin.OUT)   # commande moteur montée
pTemoin   = Pin(2,  Pin.OUT)   # LED témoin de l'étape 0 (repos)


# =============================================================================
# BANDEAU NEOPIXEL — indicateur visuel du niveau de la cabine
# =============================================================================

np = neopixel.NeoPixel(Pin(13), 8)   # 8 LEDs WS2812 sur la broche 13

# Éteindre toutes les LEDs au démarrage
for led in range(8):
    np[led] = (0, 0, 0)   # couleur noire = éteinte
np.write()                # envoyer la commande au bandeau


# =============================================================================
# INITIALISATION DU MOTEUR GRAFCET
# =============================================================================

g = Grafcet(nb_etapes=3, etape_initiale=0)
# g.etapes = [True, False, False] → seule l'étape 0 est active au démarrage
# g.tempo  = [0, 0, 0]
# g.compt  = [0, 0, 0]


# =============================================================================
# TABLE DE TRANSITIONS
# Définit la structure du GRAFCET sous forme de données.
# Format : (indice_transition, (étapes_à_désactiver,), (étapes_à_activer,))
# =============================================================================

T = [
    (0, (0,), (1,)),   # T0 : quand transitions[0]=True → désactive étape 0, active étape 1
    (1, (1,), (2,)),   # T1 : quand transitions[1]=True → désactive étape 1, active étape 2
    (2, (2,), (0,)),   # T2 : quand transitions[2]=True → désactive étape 2, active étape 0
]


# =============================================================================
# VARIABLES DE L'APPLICATION
# =============================================================================

# --- Actions (sorties logiques calculées dans gerer_actions) ---
Descendre = False   # True → activer la descente de la cabine
Monter    = False   # True → activer la montée de la cabine

# --- Entrées (lues depuis les capteurs dans lire_entrees) ---
Start = False   # True quand le bouton Start est pressé
Haut  = False   # True quand la cabine est en position haute (fin de course ou niveau simulé)
Bas   = False   # True quand la cabine est en position basse  (fin de course ou niveau simulé)

# --- Simulation physique de la cabine ---
niveau   = 0      # position simulée de la cabine : 0 = haut, -100 = bas (en unités arbitraires)
vitesse  = 1      # incrément de déplacement par cycle (augmenter pour accélérer la simulation)
x_ancien = 0      # dernière position affichée sur le NeoPixel (pour optimiser les rafraîchissements)
compt_affichage = 0   # compteur local pour limiter la fréquence de rafraîchissement de l'OLED


# =============================================================================
# FONCTION : simulation et affichage du niveau de la cabine
# =============================================================================

def ascenseur(inc):
    """
    Met à jour le niveau simulé de la cabine et rafraîchit les affichages.

    :param inc: incrément à appliquer au niveau
                  inc = -vitesse → descente (niveau diminue vers -100)
                  inc = +vitesse → montée   (niveau augmente vers 0)
    """
    global niveau, x_ancien, compt_affichage

    # --- Mise à jour du niveau simulé ---
    niveau = niveau + inc              # déplace la cabine
    if niveau < -100: niveau = -100    # butée basse : ne pas dépasser -100
    if niveau >    0: niveau =    0    # butée haute : ne pas dépasser 0

    # --- Calcul de la position sur le bandeau NeoPixel ---
    # Conversion du niveau (-100 à 0) en nombre de LEDs allumées (0 à 7)
    # niveau=0   → x=0  (cabine en haut, aucune LED)
    # niveau=-100 → x=7  (cabine en bas, 7 LEDs allumées)
    x = abs(int(-niveau / 12.6))

    # Mettre à jour le NeoPixel seulement si la position a changé (optimisation)
    if x != x_ancien:
        for led in range(0, x):   # LEDs en dessous de la cabine : allumées en vert
            np[led] = (0, 30, 0)
        for led in range(x, 8):   # LEDs au-dessus de la cabine : éteintes
            np[led] = (0, 0, 0)
        np[x] = (0, 50, 0)        # LED à la position exacte de la cabine : vert plus vif
        np.write()                # envoyer la mise à jour au bandeau
        x_ancien = x              # mémoriser la nouvelle position

    # --- Rafraîchissement de l'écran OLED (tous les 3 cycles pour limiter la charge I2C) ---
    compt_affichage += 1
    if compt_affichage == 3:
        display.fill_rect(60, 0,   60, 64, 0)           # effacer la zone de la barre (fond noir)
        display.fill_rect(60, 0,   10, -int(niveau / 2), 1)  # dessiner la barre de niveau
        # -int(niveau/2) : niveau=0 → hauteur=0px, niveau=-100 → hauteur=50px
        display.show()         # envoyer le buffer à l'écran
        compt_affichage = 0    # remettre le compteur à zéro


# =============================================================================
# PHASE 1 — GÉRER LES ACTIONS
# Calcule les variables logiques (Descendre, Monter) selon les étapes actives.
# Cette fonction NE touche PAS aux sorties physiques (c'est le rôle d'affecter_sorties).
# =============================================================================

def gerer_actions():
    global Descendre, Monter

    if g.etapes[0]:
        # ÉTAPE 0 — Repos : aucun mouvement, réinitialisation des commandes
        Descendre = False
        Monter    = False
        # Note : g.tempo[0] est incrémenté automatiquement par g.tick()
        # La LED témoin reflète l'état de l'étape 0 (voir affecter_sorties)

    if g.etapes[1]:
        # ÉTAPE 1 — Descente : activer la commande de descente
        Descendre = True
        Monter    = False

    if g.etapes[2]:
        # ÉTAPE 2 — Montée : activer la commande de montée
        Descendre = False
        Monter    = True


# =============================================================================
# PHASE 2 — AFFECTER LES SORTIES
# Applique les variables logiques sur les sorties physiques (broches, LEDs, moteurs).
# Séparer cette phase de gerer_actions permet de tester la logique sans matériel.
# =============================================================================

def affecter_sorties():
    pDescente.value(Descendre)              # commande moteur descente (True=actif, False=arrêt)
    pMontee.value(Monter)                   # commande moteur montée
    pTemoin.value(g.etapes[0])              # LED témoin allumée uniquement à l'étape 0 (repos)

    if Descendre: ascenseur(-vitesse)       # simulation : descendre d'un cran
    if Monter:    ascenseur(+vitesse)       # simulation : monter d'un cran


# =============================================================================
# PHASE 3 — LIRE LES ENTRÉES
# Lit les capteurs et boutons, met à jour les variables d'entrée logiques.
# Les fins de course physiques sont complétées par les limites de la simulation.
# =============================================================================

def lire_entrees():
    global Start, Haut, Bas

    Start = pStart.value()   # bouton Start : 1 si pressé

    # Fin de course BAS : actif si le capteur physique détecte la position,
    # OU si la simulation a atteint le niveau plancher (-100)
    Bas   = pBas.value()  or (niveau <= -99)

    # Fin de course HAUT : actif si le capteur physique détecte la position,
    # OU si la simulation a atteint le niveau plafond (0)
    Haut  = pHaut.value() or (niveau >= -1)


# =============================================================================
# PHASE 4 — CALCULER LES TRANSITIONS
# Évalue les réceptivités (conditions logiques) pour chaque transition.
# Le résultat est stocké dans la liste `transitions`, indexée comme T.
# =============================================================================

def calculer_transitions():
    global transitions

    # T0 : franchissable si l'étape 0 est active ET Start pressé ET tempo > 200ms
    # Le délai tempo > 200ms évite un démarrage immédiat (anti-rebond logiciel)
    transitions[0] = g.etapes[0] and Start and (g.tempo[0] > 200)

    # T1 : franchissable si l'étape 1 est active ET fin de course basse atteinte
    transitions[1] = g.etapes[1] and Bas

    # T2 : franchissable si l'étape 2 est active ET fin de course haute atteinte
    transitions[2] = g.etapes[2] and Haut


# Initialisation du tableau des transitions (une entrée par transition dans T)
transitions = [False] * len(T)


# =============================================================================
# BOUCLE PRINCIPALE — cycle GRAFCET normalisé
# Chaque itération représente un cycle automate d'environ 20 ms.
# =============================================================================

while True:

    g.tick(20)               # 1. Mise à jour des timers (incrémente tempo des étapes actives)

    gerer_actions()          # 2. Calcul des actions selon les étapes actives

    affecter_sorties()       # 3. Application des actions sur les sorties physiques

    lire_entrees()           # 4. Lecture des capteurs et boutons

    calculer_transitions()   # 5. Évaluation des réceptivités

    g.franchir(T, transitions)  # 6. Franchissement des transitions validées → mise à jour des étapes

    synchro_ms(20)           # 7. Attente de fin de cycle (synchronisation à 20 ms)
