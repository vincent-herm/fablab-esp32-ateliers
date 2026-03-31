# =============================================================================
# demo_complet.py — Démonstration GRAFCET complète (10 étapes)
# =============================================================================
# Exemple pédagogique utilisant TOUTES les fonctionnalités du moteur
# grafcet_complet.py sur carte ENIM. Pas de système réaliste — c'est
# un parcours qui montre chaque feature du GRAFCET.
#
# FONCTIONNALITÉS DÉMONTRÉES :
#
#   ┌─────────────────────────────────────────────────────────────────────┐
#   │ Fonctionnalité              │ Où dans le code                      │
#   ├─────────────────────────────┼──────────────────────────────────────┤
#   │ LED qui respire (PWM)       │ led_bleue PWM sinus en étape 0      │
#   │ LED qui clignote            │ led_rouge 2 Hz (étapes 1 à 8)       │
#   │ Mode CONTINU                │ led_bleue, led_verte, led_jaune     │
#   │ Mode MÉMORISÉ (SET/RESET)   │ led_rouge : SET rising[1],          │
#   │                             │ RESET rising[9]. Buzzer rising[0].  │
#   │ Front montant d'entrée (fm) │ bpA=fm[0], bpD=fm[1], tp1=fm[2],   │
#   │                             │ tp2=fm[3]                           │
#   │ Front montant d'étape       │ rising[0]=bip, rising[1]=SET,       │
#   │                             │ rising[9]=RESET                     │
#   │ Front descendant d'étape    │ falling[3]/falling[4]=affiche compt │
#   │ Temporisation (tempo)       │ tempo[0]>500, tempo[1]>2000,        │
#   │                             │ tempo[3]>1500, tempo[4]>1500,       │
#   │                             │ tempo[9]>3000                       │
#   │ Compteur d'étape (compt)    │ compt[3] et compt[4] : appuis bpA   │
#   │ Divergence ET               │ T1 → étapes 2 et 6 en parallèle    │
#   │ Convergence ET              │ T8 ← étapes 5 et 8 simultanées     │
#   │ Divergence OU               │ T2 (bpB) / T3 (bpC) depuis étape 2 │
#   │ Convergence OU              │ T4/T5 → étape 5                    │
#   │ TouchPad                    │ tp1 (T6), tp2 (T7)                 │
#   │ Réinitialisation            │ bpD (fm[1]) → reinitialiser()       │
#   │ Validation auto (Règle 2)   │ réceptivités pures                  │
#   └─────────────────────────────┴──────────────────────────────────────┘
#
# ENTRÉES :
#   bpA  (Pin 25) → Start + comptage (front montant fm[0])
#   bpB  (Pin 34) → Divergence OU : choix gauche (niveau)
#   bpC  (Pin 39) → Divergence OU : choix droit (niveau)
#   bpD  (Pin 36) → Arrêt d'urgence (front montant fm[1])
#   tp1  (Pin 15) → TouchPad 1 : branche droite (front montant fm[2])
#   tp2  (Pin  4) → TouchPad 2 : suite droite (front montant fm[3])
#
# SORTIES :
#   led_bleue (Pin  2) → respire en veille (PWM), fixe sinon   [CONTINU]
#   led_verte (Pin 18) → branche gauche                        [CONTINU]
#   led_jaune (Pin 19) → branche droite                        [CONTINU]
#   led_rouge (Pin 23) → clignote 2 Hz étapes 1-8              [MÉMORISÉ]
#   buzzer    (Pin  5) → bip au démarrage/retour                [MÉMORISÉ]
#   NeoPixel  (Pin 26) → indicateur de choix/progression
#
# GRAFCET (10 étapes) :
#
#   Étape 0 — Veille : LED bleue respire, bip buzzer (rising)
#       │ T0 : fm[0] + tempo > 500
#   Étape 1 — Démarrage : LED bleue fixe, SET clignote rouge (rising)
#       │ T1 : tempo > 2000 → DIVERGENCE ET
#       ├────────────────────────────────────┐
#   Étape 2 — Branche G : LED verte ON      Étape 6 — Branche D : LED jaune ON
#       │ DIVERGENCE OU                          │ T6 : fm tp1
#       ├───────────┐                        Étape 7 — Suite : NeoPixel vert
#   T2:bpB      T3:bpC                          │ T7 : fm tp2
#       │           │                        Étape 8 — Fin D (attente conv. ET)
#   Étape 3      Étape 4                        │
#   NP rouge     NP bleu                        │
#   compt++      compt++                         │
#       │ T4:1.5s   │ T5:1.5s                   │
#       └───────────┘                            │
#       CONVERGENCE OU                           │
#       │                                        │
#   Étape 5 — Fin G (attente conv. ET)           │
#       └──────── T8 : CONVERGENCE ET ───────────┘
#       │
#   Étape 9 — Finale : RESET clignote, buzzer, 3s
#       │ T9 : tempo > 3000 → retour Étape 0
#
#   À tout moment : fm[1] (bpD) → reinitialiser()
#
# Fichiers nécessaires sur l'ESP32 :
#   grafcet_complet.py, essential.py
# =============================================================================

from machine import Pin, PWM
from math import sin, pi
from time import ticks_ms
from grafcet_complet import Grafcet

from essential import (
    synchro_ms,
    bpA, bpB, bpC, bpD,
    tp1, tp2,
    led_bleue, led_verte, led_jaune, led_rouge,
    buzzer, np,
)

# LED bleue en PWM pour la respiration
pwm_bleue = PWM(Pin(2), freq=1000, duty=0)


# =============================================================================
# GRAFCET — 10 étapes
# =============================================================================

# nb_fronts=4 : bpA(0), bpD(1), tp1(2), tp2(3)
g = Grafcet(nb_etapes=10, nb_fronts=4)

T = [
    (0, (0,),    (1,)),     # T0 : Veille → Démarrage
    (1, (1,),    (2, 6)),   # T1 : Démarrage → DIVERGENCE ET (branches G et D)
    (2, (2,),    (3,)),     # T2 : bpB → Choix Gauche (DIVERGENCE OU)
    (3, (2,),    (4,)),     # T3 : bpC → Choix Droit  (DIVERGENCE OU)
    (4, (3,),    (5,)),     # T4 : Choix G → Fin gauche
    (5, (4,),    (5,)),     # T5 : Choix D → Fin gauche (CONVERGENCE OU)
    (6, (6,),    (7,)),     # T6 : tp1 → Suite droite
    (7, (7,),    (8,)),     # T7 : tp2 → Fin droite
    (8, (5, 8),  (9,)),     # T8 : CONVERGENCE ET → Finale
    (9, (9,),    (0,)),     # T9 : Finale → retour Veille
]

transitions = [False] * len(T)


# =============================================================================
# VARIABLES
# =============================================================================

clignoter   = False   # LED rouge clignote (mémorisé SET/RESET)
nb_parcours = -1      # compteur de parcours (-1 : le rising[0] du démarrage ne compte pas)

# NeoPixel éteint au démarrage
for i in range(8):
    np[i] = (0, 0, 0)
np.write()


# =============================================================================
# CYCLE GRAFCET
# =============================================================================

def gerer_actions():
    global clignoter, nb_parcours

    # --- LED bleue : respire en veille (PWM sinus), fixe sinon [CONTINU] ---
    if g.etapes[0]:
        # Respiration : duty varie sinusoïdalement, période 2 secondes
        duty = int(511 + 511 * sin(g.tempo[0] * pi / 1000))
        pwm_bleue.duty(duty)
    elif g.etapes[1]:
        pwm_bleue.duty(1023)     # fixe ON pendant le démarrage
    else:
        pwm_bleue.duty(0)        # éteinte sinon

    # --- LED verte : branche gauche [CONTINU] ---
    led_verte.value(g.etapes[2] or g.etapes[3] or g.etapes[4])

    # --- LED jaune : branche droite [CONTINU] ---
    led_jaune.value(g.etapes[6] or g.etapes[7])

    # --- Bip buzzer "système prêt" (rising[0]) [MÉMORISÉ] ---
    if g.rising[0]:
        buzzer.init(freq=1000, duty=50)
    if g.etapes[0] and g.tempo[0] > 200:
        buzzer.deinit()

    # --- LED rouge clignote (SET/RESET — traverse étapes 1 à 8) [MÉMORISÉ] ---
    if g.rising[1]:    clignoter = True      # SET : début du parcours
    if g.rising[9]:    clignoter = False     # RESET : arrivée en finale

    # --- Buzzer double bip en finale [MÉMORISÉ] ---
    if g.rising[9]:
        buzzer.init(freq=1500, duty=50)
    if g.etapes[9] and g.tempo[9] > 100:
        buzzer.deinit()
    if g.etapes[9] and g.tempo[9] > 300:
        buzzer.init(freq=1500, duty=50)
    if g.etapes[9] and g.tempo[9] > 400:
        buzzer.deinit()

    # --- NeoPixel : indicateur visuel selon l'étape [CONTINU] ---
    if g.rising[3]:
        for i in range(4): np[i] = (30, 0, 0)       # choix G : rouge à gauche
        for i in range(4, 8): np[i] = (0, 0, 0)
        np.write()
    if g.rising[4]:
        for i in range(4): np[i] = (0, 0, 0)
        for i in range(4, 8): np[i] = (0, 0, 30)    # choix D : bleu à droite
        np.write()
    if g.rising[7]:
        for i in range(8): np[i] = (0, 30, 0)        # suite droite : tout vert
        np.write()
    if g.rising[9]:
        for i in range(8): np[i] = (30, 30, 0)       # finale : tout jaune
        np.write()
    if g.rising[0]:
        for i in range(8): np[i] = (0, 0, 0)         # veille : tout éteint
        np.write()

    # --- Compteurs d'étape : appuis bpA pendant les choix ---
    if g.etapes[3] and g.fm[0]:
        g.compt[3] += 1
    if g.etapes[4] and g.fm[0]:
        g.compt[4] += 1
    if g.falling[3]:
        print("  Appuis bpA pendant choix gauche :", g.compt_final[3])
    if g.falling[4]:
        print("  Appuis bpA pendant choix droit :", g.compt_final[4])

    # --- Compteur de parcours ---
    if g.rising[0]:
        nb_parcours += 1
        if nb_parcours > 0:
            print("Parcours", nb_parcours, "terminé")


def affecter_sorties():
    # LED rouge : clignotement 2 Hz (mémorisé)
    if clignoter:
        led_rouge.value(ticks_ms() % 500 < 250)
    else:
        led_rouge.value(0)


def lire_entrees():
    # Fronts d'entrée : bpA(0), bpD(1), tp1(2), tp2(3)
    g.entrees[0] = bpA.value()
    g.entrees[1] = bpD.value()
    g.entrees[2] = tp1.read() < 350     # TouchPad touché
    g.entrees[3] = tp2.read() < 350     # TouchPad touché


def calculer_transitions():
    # Réceptivités pures — le moteur vérifie les étapes sources (Règle 2)
    transitions[0] = g.fm[0] and (g.tempo[0] > 500)    # front bpA + anti-rebond
    transitions[1] = g.tempo[1] > 2000                   # attente 2 secondes
    transitions[2] = bpB.value()                          # divergence OU : gauche
    transitions[3] = bpC.value()                          # divergence OU : droite
    transitions[4] = g.tempo[3] > 1500                    # fin choix gauche (1.5s)
    transitions[5] = g.tempo[4] > 1500                    # fin choix droit (1.5s)
    transitions[6] = g.fm[2]                              # front tp1 (toucher)
    transitions[7] = g.fm[3]                              # front tp2 (toucher)
    transitions[8] = True                                  # convergence ET (validation auto)
    transitions[9] = g.tempo[9] > 3000                    # fin finale (3s)


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

print("=== GRAFCET Démonstration complète (10 étapes) ===")
print("bpA=Start  bpB=Choix G  bpC=Choix D  bpD=AU")
print("tp1=Branche droite  tp2=Suite droite")
print()
print("Parcours : Veille → Démarrage (2s)")
print("  Branche G : bpB ou bpC → choix (1.5s)")
print("  Branche D : tp1 → tp2")
print("  Convergence ET → Finale (3s) → retour Veille")
print()

while True:

    g.franchir(T, transitions)

    # Arrêt d'urgence
    if g.fm[1]:
        g.reinitialiser()
        clignoter = False
        nb_parcours = -1
        led_rouge.value(0)
        buzzer.deinit()
        pwm_bleue.duty(0)
        for i in range(8): np[i] = (0, 0, 0)
        np.write()
        print("!!! ARRÊT D'URGENCE !!!")

    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    g.detecter_fronts_entrees()
    calculer_transitions()
    synchro_ms(20)
