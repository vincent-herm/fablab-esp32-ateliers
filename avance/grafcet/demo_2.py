# =============================================================================
# demo_complet.py — Démonstration GRAFCET complète (12 étapes)
# =============================================================================
# Exemple pédagogique utilisant TOUTES les fonctionnalités du moteur
# grafcet_complet.py sur carte ENIM. Pas de système réaliste — c'est
# un parcours conçu pour montrer chaque feature du GRAFCET.
#
# FONCTIONNALITÉS DÉMONTRÉES :
#
#   ┌─────────────────────────────────────────────────────────────────────┐
#   │ Fonctionnalité               │ Où dans le code                     │
#   ├──────────────────────────────┼─────────────────────────────────────┤
#   │ Mode CONTINU [C]             │ led_bleue, led_verte, led_jaune,    │
#   │                              │ NeoPixel, OLED selon étape          │
#   │ Mode MÉMORISÉ [M] SET/RESET  │ led_rouge : SET rising[1],          │
#   │                              │   RESET rising[9]                   │
#   │                              │ chenillard_actif : SET rising[9],   │
#   │                              │   RESET rising[11]                  │
#   │                              │ Buzzer one-shot (rising[0/9])       │
#   │ Front montant d'étape        │ rising[0] bip, rising[1] SET rouge, │
#   │   (rising)                   │   rising[9] SET chenillard + RESET  │
#   │                              │   rouge, rising[11] RESET cheni.    │
#   │ Front descendant d'étape     │ falling[3]/[4] : sauvegarde tempo   │
#   │   (falling)                  │   pour meilleur temps               │
#   │ Front montant d'entrée (fm)  │ bpA=fm[0], bpD=fm[1],              │
#   │                              │   tp1=fm[2], tp2=fm[3]              │
#   │ Front descendant d'entrée    │ fd[0] (relâcher bpA) : skip bilan  │
#   │   (fd)                       │                                     │
#   │ Temporisation (tempo)        │ É0>500, É1>2000, É3>1500, É4>1500, │
#   │                              │   É9>1500, É10>3000, É11>2000      │
#   │ Compteur d'étape (compt)     │ compt[3]/[4] : appuis bpA          │
#   │ Compteur inter-cycles        │ nb_parcours (variable Python)       │
#   │ Sauvegarde tempo (external)  │ _tempo3_sauve → meilleur_temps G   │
#   │ Divergence ET                │ T1 → étapes 2 et 6 en parallèle   │
#   │ Convergence ET               │ T8 ← étapes 5 et 8                │
#   │ Divergence OU                │ T2 (bpB) / T3 (bpC) depuis É2     │
#   │ Convergence OU               │ T4/T5 → étape 5                   │
#   │ Réinitialisation             │ bpD (fm[1]) → reinitialiser()      │
#   │ Validation auto (Règle 2)    │ réceptivités pures dans calc_trans │
#   │ OLED temps réel              │ countdown É1, labels É2/É6,        │
#   │                              │   chenillard barre É10, bilan É11  │
#   │ NeoPixel chenillard          │ 1 LED qui tourne pendant É10       │
#   └──────────────────────────────┴─────────────────────────────────────┘
#
# ENTRÉES :
#   bpA  (Pin 25) → Start + comptage appuis (fm[0]) + skip bilan (fd[0])
#   bpB  (Pin 34) → Divergence OU gauche (niveau)
#   bpC  (Pin 39) → Divergence OU droite (niveau)
#   bpD  (Pin 36) → Arrêt d'urgence (fm[1])
#   tp1  (Pin 15) → TouchPad 1 branche droite (fm[2])
#   tp2  (Pin  4) → TouchPad 2 suite droite (fm[3])
#
# SORTIES :
#   led_bleue (Pin  2) → respire en veille (PWM), fixe sinon      [C]
#   led_verte (Pin 18) → active sur branches G (É2, É3, É4)       [C]
#   led_jaune (Pin 19) → active sur branche D (É6, É7)            [C]
#   led_rouge (Pin 23) → clignote 2 Hz de É1 à É8                 [M]
#   buzzer    (Pin  5) → bip prêt (rising[0]), double bip (É9)    [M]
#   NeoPixel  (Pin 26) → couleurs selon branche + chenillard É10  [C/M]
#   OLED      (I2C)   → countdown, labels, chenillard, bilan      [C]
#
# GRAFCET (12 étapes) :
#
#   Étape 0 — Veille
#     [C] LED bleue respire (PWM sinus) | OLED "PRÊT + nb parcours"
#     [M] Bip buzzer 200 ms (rising[0]) | NeoPixel éteint
#       │ T0 : fm[0] + tempo > 500
#   Étape 1 — Démarrage
#     [C] LED bleue fixe ON | OLED compte à rebours 2...1...GO!
#     [M] SET led_rouge clignote (rising[1])
#       │ T1 : tempo > 2000 → DIVERGENCE ET
#       ├──────────────────────────────────────────────┐
#   Étape 2 — Branche G                          Étape 6 — Branche D
#     [C] LED verte ON | OLED "Branche G"          [C] LED jaune ON | OLED "Branche D"
#       │ DIVERGENCE OU                               │ T6 : fm[2] (tp1)
#       ├────────────┐                           Étape 7 — Suite D
#     T2:bpB      T3:bpC                           [C] NeoPixel tout vert
#       │            │                               [C] OLED "touche tp2"
#   Étape 3        Étape 4                           │ T7 : fm[3] (tp2)
#     [C] NP rouge   [C] NP bleu               Étape 8 — Fin D (attente)
#     [C] compt bpA  [C] compt bpA               [C] OLED "synchro..."
#       │ T4:1.5s      │ T5:1.5s                    │
#       └──────────────┘                             │
#       CONVERGENCE OU                               │
#   Étape 5 — Fin G (attente conv. ET)               │
#       └─────────── T8 : CONVERGENCE ET ────────────┘
#   Étape 9 — Finale
#     [M] RESET led_rouge (rising[9])
#     [M] SET chenillard_actif (rising[9])
#     [M] Buzzer double bip (rising[9])
#     [C] NeoPixel tout jaune | OLED "BRAVO!"
#       │ T9 : tempo > 1500
#   Étape 10 — Chenillard [NEW]
#     [C] NeoPixel : 1 LED tourne (toutes les 150 ms)
#     [C] OLED : barre blanche rebondissante (chenillard barre)
#       │ T10 : tempo > 3000
#   Étape 11 — Bilan [NEW]
#     [M] RESET chenillard_actif (rising[11])
#     [C] OLED : bilan (nb_parcours, meilleur temps G)
#     [C] NeoPixel éteint
#       │ T11 : tempo > 2000 OU fd[0] (bpA relâché = skip)
#
#   À tout moment : fm[1] (bpD) → reinitialiser()
#
# Fichiers nécessaires sur l'ESP32 :
#   grafcet_complet.py, essential.py, ssd1306.py
# =============================================================================

from machine import Pin, PWM, I2C
from math import sin, pi
from time import ticks_ms
import ssd1306
from grafcet_complet import Grafcet

from essential import (
    synchro_ms,
    bpA, bpB, bpC, bpD,
    tp1, tp2,
    led_bleue, led_verte, led_jaune, led_rouge,
    buzzer, np,
)

# --- OLED SSD1306 128x64 sur I2C(0) SDA=21 SCL=22 ---
i2c  = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# LED bleue en PWM pour la respiration en veille
pwm_bleue = PWM(Pin(2), freq=1000, duty=0)


# =============================================================================
# GRAFCET — 12 étapes
# =============================================================================

# nb_fronts=4 : bpA(0), bpD(1), tp1(2), tp2(3)
g = Grafcet(nb_etapes=12, nb_fronts=4)

T = [
    (0,  (0,),    (1,)),      # T0  : Veille → Démarrage
    (1,  (1,),    (2, 6)),    # T1  : Démarrage → DIVERGENCE ET (G + D)
    (2,  (2,),    (3,)),      # T2  : bpB → Choix Gauche  (DIVERGENCE OU)
    (3,  (2,),    (4,)),      # T3  : bpC → Choix Droite  (DIVERGENCE OU)
    (4,  (3,),    (5,)),      # T4  : Fin choix G (1.5 s)
    (5,  (4,),    (5,)),      # T5  : Fin choix D (1.5 s)  (CONVERGENCE OU)
    (6,  (6,),    (7,)),      # T6  : fm tp1 → Suite droite
    (7,  (7,),    (8,)),      # T7  : fm tp2 → Fin droite
    (8,  (5, 8),  (9,)),      # T8  : CONVERGENCE ET → Finale
    (9,  (9,),    (10,)),     # T9  : Finale → Chenillard   [NEW]
    (10, (10,),   (11,)),     # T10 : Chenillard → Bilan    [NEW]
    (11, (11,),   (0,)),      # T11 : Bilan → retour Veille
]

transitions = [False] * len(T)


# =============================================================================
# VARIABLES
# =============================================================================

clignoter        = False  # [M] LED rouge (SET rising[1], RESET rising[9])
chenillard_actif = False  # [M] OLED chenillard (SET rising[9], RESET rising[11])
nb_parcours      = -1     # compteur inter-cycles (-1 : rising[0] initial ignoré)
_tempo3_sauve    = 0      # dernier tempo[3] connu (mis à jour chaque cycle)
_tempo4_sauve    = 0      # dernier tempo[4] connu
meilleur_temps_G = 0      # meilleur temps branche G (ms)
_dernier_compte  = -1     # pour rafraîchir OLED countdown seulement quand ça change
_oled_step       = -1     # étape OLED affichée (évite les re-draw inutiles)

# NeoPixel éteint au démarrage
for i in range(8):
    np[i] = (0, 0, 0)
np.write()

# OLED : écran de bienvenue
oled.fill(0)
oled.text("GRAFCET Demo", 0, 0)
oled.text("12 etapes", 0, 16)
oled.text("bpA = Start", 0, 40)
oled.show()


# =============================================================================
# FONCTIONS OLED (helpers)
# =============================================================================

def oled_veille(nb):
    oled.fill(0)
    oled.text("== PRET ==", 18, 4)
    oled.text("bpA pour demarrer", 0, 22)
    if nb > 0:
        oled.text("Parcours: " + str(nb), 0, 42)
    oled.show()

def oled_countdown(secondes):
    oled.fill(0)
    oled.text("DEMARRAGE", 20, 4)
    if secondes > 0:
        oled.text(str(secondes) + "...", 52, 30)
    else:
        oled.text("GO!", 52, 30)
    oled.show()

def oled_branche(label):
    oled.fill(0)
    oled.text(label, 0, 4)
    oled.show()

def oled_bravo():
    oled.fill(0)
    oled.text("*** BRAVO! ***", 4, 4)
    oled.text("Parcours " + str(nb_parcours + 1), 0, 28)
    oled.show()

def oled_chenillard(tempo):
    """Barre blanche rebondissante + texte."""
    LARGEUR_BARRE = 20
    PLAGE = 128 - LARGEUR_BARRE          # 108 px de course
    PERIODE = 2000                        # rebond toutes les 2 s
    t_mod = tempo % PERIODE
    if t_mod < PERIODE // 2:
        x = int(t_mod / (PERIODE // 2) * PLAGE)
    else:
        x = PLAGE - int((t_mod - PERIODE // 2) / (PERIODE // 2) * PLAGE)
    oled.fill(0)
    oled.text("Chenillard", 20, 4)
    # Barre rebondissante sur la ligne du bas
    oled.fill_rect(x, 48, LARGEUR_BARRE, 10, 1)
    oled.show()

def oled_bilan(nb, meilleur):
    oled.fill(0)
    oled.text("== BILAN ==", 16, 0)
    oled.text("Parcours: " + str(nb), 0, 18)
    if meilleur > 0:
        oled.text("Meilleur G:", 0, 34)
        oled.text(str(meilleur // 1000) + "." + str((meilleur % 1000) // 100) + " s", 0, 46)
    else:
        oled.text("(pas de temps G)", 0, 40)
    oled.text("bpA=skip", 80, 56)
    oled.show()


# =============================================================================
# CYCLE GRAFCET
# =============================================================================

def gerer_actions():
    global clignoter, chenillard_actif, nb_parcours
    global _tempo3_sauve, _tempo4_sauve, meilleur_temps_G
    global _dernier_compte, _oled_step

    # -----------------------------------------------------------------------
    # LED bleue : respire en veille (PWM sinus), fixe pendant démarrage [C]
    # -----------------------------------------------------------------------
    if g.etapes[0]:
        duty = int(511 + 511 * sin(g.tempo[0] * pi / 1000))
        pwm_bleue.duty(duty)
    elif g.etapes[1]:
        pwm_bleue.duty(1023)
    else:
        pwm_bleue.duty(0)

    # -----------------------------------------------------------------------
    # LED verte : branches G [C]
    # -----------------------------------------------------------------------
    led_verte.value(g.etapes[2] or g.etapes[3] or g.etapes[4])

    # -----------------------------------------------------------------------
    # LED jaune : branche D [C]
    # -----------------------------------------------------------------------
    led_jaune.value(g.etapes[6] or g.etapes[7])

    # -----------------------------------------------------------------------
    # Buzzer "système prêt" — bip 200 ms (rising[0]) [M]
    # -----------------------------------------------------------------------
    if g.rising[0]:
        buzzer.init(freq=880, duty=50)
    if g.etapes[0] and g.tempo[0] > 200:
        buzzer.deinit()

    # -----------------------------------------------------------------------
    # LED rouge clignote — SET rising[1], RESET rising[9] [M]
    # -----------------------------------------------------------------------
    if g.rising[1]:
        clignoter = True
    if g.rising[9]:
        clignoter = False

    # -----------------------------------------------------------------------
    # Buzzer double bip en finale (rising[9]) [M]
    # -----------------------------------------------------------------------
    if g.rising[9]:
        buzzer.init(freq=1500, duty=50)
    if g.etapes[9] and g.tempo[9] > 100:
        buzzer.deinit()
    if g.etapes[9] and g.tempo[9] > 300:
        buzzer.init(freq=1800, duty=50)
    if g.etapes[9] and g.tempo[9] > 450:
        buzzer.deinit()

    # -----------------------------------------------------------------------
    # Chenillard mémorisé — SET rising[9], RESET rising[11] [M]
    # -----------------------------------------------------------------------
    if g.rising[9]:
        chenillard_actif = True
    if g.rising[11]:
        chenillard_actif = False

    # -----------------------------------------------------------------------
    # NeoPixel — actions sur fronts d'étape [C/M]
    # -----------------------------------------------------------------------
    if g.rising[0]:                              # retour veille : éteindre
        for i in range(8): np[i] = (0, 0, 0)
        np.write()
    if g.rising[3]:                              # choix G : 4 LEDs rouges
        for i in range(4): np[i] = (30, 0, 0)
        for i in range(4, 8): np[i] = (0, 0, 0)
        np.write()
    if g.rising[4]:                              # choix D : 4 LEDs bleues
        for i in range(4): np[i] = (0, 0, 0)
        for i in range(4, 8): np[i] = (0, 0, 30)
        np.write()
    if g.rising[7]:                              # suite droite : tout vert
        for i in range(8): np[i] = (0, 30, 0)
        np.write()
    if g.rising[9]:                              # finale : tout jaune
        for i in range(8): np[i] = (30, 30, 0)
        np.write()

    # Chenillard NeoPixel pendant É10 : 1 LED orange qui tourne [C]
    if g.etapes[10]:
        pos = (g.tempo[10] // 150) % 8          # change toutes les 150 ms
        for i in range(8):
            np[i] = (40, 20, 0) if i == pos else (0, 0, 0)
        np.write()

    if g.rising[11]:                             # bilan : NeoPixel éteint
        for i in range(8): np[i] = (0, 0, 0)
        np.write()

    # -----------------------------------------------------------------------
    # OLED — mise à jour selon l'étape active [C]
    # -----------------------------------------------------------------------
    if g.rising[0]:
        oled_veille(nb_parcours)
        _oled_step = 0

    if g.rising[1]:
        _dernier_compte = -1               # force le premier affichage
        _oled_step = 1

    if g.etapes[1]:                        # countdown : rafraîchit chaque seconde
        compte = max(0, 2 - g.tempo[1] // 1000)
        if compte != _dernier_compte:
            _dernier_compte = compte
            oled_countdown(compte)

    if g.rising[2]: oled_branche("Branche G")
    if g.rising[6]: oled_branche("Branche D")
    if g.rising[7]:
        oled.fill(0)
        oled.text("Branche D", 0, 4)
        oled.text("Touche tp2...", 0, 24)
        oled.show()
    if g.rising[8]:
        oled.fill(0)
        oled.text("Synchro ET...", 0, 24)
        oled.show()
    if g.rising[5]:
        oled.fill(0)
        oled.text("Synchro ET...", 0, 24)
        oled.show()
    if g.rising[9]:
        oled_bravo()

    # Chenillard OLED : rafraîchit toutes les 60 ms pendant É10
    if g.etapes[10] and g.tempo[10] % 60 < 20:
        oled_chenillard(g.tempo[10])

    if g.rising[11]:
        oled_bilan(nb_parcours, meilleur_temps_G)

    # -----------------------------------------------------------------------
    # Compteur d'appuis bpA dans les étapes 3 et 4 [C]
    # -----------------------------------------------------------------------
    if g.etapes[3] and g.fm[0]:
        g.compt[3] += 1
    if g.etapes[4] and g.fm[0]:
        g.compt[4] += 1

    # -----------------------------------------------------------------------
    # Sauvegarde tempo[3] et tempo[4] chaque cycle (pour meilleur_temps) [C]
    # (franchir() remet tempo à 0 avant que falling soit lisible)
    # -----------------------------------------------------------------------
    if g.etapes[3]:
        _tempo3_sauve = g.tempo[3]
    if g.etapes[4]:
        _tempo4_sauve = g.tempo[4]

    # -----------------------------------------------------------------------
    # Sur falling[3]/[4] : afficher appuis et calculer meilleur temps [M]
    # -----------------------------------------------------------------------
    if g.falling[3]:
        print("  Appuis bpA (branche G-gauche) :", g.compt_final[3])
        t = _tempo3_sauve
        if meilleur_temps_G == 0 or t < meilleur_temps_G:
            meilleur_temps_G = t
            print("  Nouveau meilleur temps G :", t, "ms")
    if g.falling[4]:
        print("  Appuis bpA (branche G-droite) :", g.compt_final[4])
        t = _tempo4_sauve
        if meilleur_temps_G == 0 or t < meilleur_temps_G:
            meilleur_temps_G = t
            print("  Nouveau meilleur temps G :", t, "ms")

    # -----------------------------------------------------------------------
    # Compteur de parcours (rising[0] = retour en veille) [M]
    # -----------------------------------------------------------------------
    if g.rising[0]:
        nb_parcours += 1
        if nb_parcours > 0:
            print("Parcours", nb_parcours, "termine")


def affecter_sorties():
    # LED rouge : clignotement 2 Hz [M]
    if clignoter:
        led_rouge.value(ticks_ms() % 500 < 250)
    else:
        led_rouge.value(0)


def lire_entrees():
    g.entrees[0] = bpA.value()
    g.entrees[1] = bpD.value()
    g.entrees[2] = tp1.read() < 350     # TouchPad touché
    g.entrees[3] = tp2.read() < 350     # TouchPad touché


def calculer_transitions():
    # Réceptivités pures — le moteur vérifie les étapes sources (Règle 2)
    transitions[0]  = g.fm[0] and (g.tempo[0] > 500)   # front bpA + anti-rebond
    transitions[1]  = g.tempo[1] > 2000                  # attente 2 s
    transitions[2]  = bpB.value()                         # div OU : gauche
    transitions[3]  = bpC.value()                         # div OU : droite
    transitions[4]  = g.tempo[3] > 1500                   # fin choix G-gauche
    transitions[5]  = g.tempo[4] > 1500                   # fin choix G-droite
    transitions[6]  = g.fm[2]                             # front tp1
    transitions[7]  = g.fm[3]                             # front tp2
    transitions[8]  = True                                 # conv ET (validation auto)
    transitions[9]  = g.tempo[9] > 1500                   # finale (1.5 s)
    transitions[10] = g.tempo[10] > 3000                  # chenillard (3 s)
    transitions[11] = g.tempo[11] > 2000 or g.fd[0]      # bilan (2 s) ou skip bpA [fd]


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

print("=== GRAFCET Demo complète (12 étapes) ===")
print("bpA=Start/Skip  bpB=ChoixG  bpC=ChoixD  bpD=AU")
print("tp1=BrancheD  tp2=SuiteD")
print()
print("Parcours :")
print("  Veille (bpA) → Démarrage 2s → DIVERGENCE ET")
print("    Branche G : bpB ou bpC → 1.5s → attente CONV ET")
print("    Branche D : tp1 → tp2  → attente CONV ET")
print("  Finale → Chenillard 3s → Bilan 2s (bpA pour skipper)")
print("  → retour Veille")
print()

while True:

    g.franchir(T, transitions)

    # Arrêt d'urgence (hors GRAFCET — conforme à la note du moteur)
    if g.fm[1]:
        g.reinitialiser()
        clignoter        = False
        chenillard_actif = False
        nb_parcours      = -1
        meilleur_temps_G = 0
        led_rouge.value(0)
        buzzer.deinit()
        pwm_bleue.duty(0)
        for i in range(8): np[i] = (0, 0, 0)
        np.write()
        oled.fill(0)
        oled.text("!!! ARRET !!!", 16, 20)
        oled.text("bpA pour relancer", 0, 42)
        oled.show()
        print("!!! ARRET D'URGENCE !!!")

    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    g.detecter_fronts_entrees()
    calculer_transitions()
    synchro_ms(20)
