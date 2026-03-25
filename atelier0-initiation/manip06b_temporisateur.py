# Manipulation 06b — Temporisateur (minuterie d'escalier)
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# Jusqu'ici, la LED suivait le bouton en temps réel (manip 06) :
# on appuyait → allumée, on relâchait → éteinte.
#
# Ici on change de logique : on appuie UNE FOIS sur le bouton,
# la LED s'allume 5 secondes, puis s'éteint toute seule.
# C'est exactement le fonctionnement d'une minuterie d'escalier.
#
# Concept nouveau : détecter le FRONT DESCENDANT du bouton.
# Un "front" = le moment où l'état CHANGE (0→1 ou 1→0).
# On ne réagit pas à l'état "en cours", mais au changement d'état.
#
#   etat_precedent = 1 (relâché)
#   etat_actuel    = 0 (appuyé)   → FRONT DESCENDANT → on déclenche !
#
# Rien à brancher — LED GPIO 2, bouton BOOT GPIO 0.
# -----------------------------------------------------------------------

from machine import Pin    # pour contrôler les broches
import time                # pour les pauses et le chronomètre

DUREE_SECONDES = 5         # durée d'allumage en secondes (modifiable)

led    = Pin(2, Pin.OUT)              # LED intégrée en sortie
bouton = Pin(0, Pin.IN, Pin.PULL_UP)  # bouton BOOT en entrée

led.off()                  # s'assurer que la LED est éteinte au démarrage

# On mémorise l'état précédent du bouton pour détecter les changements
etat_precedent = bouton.value()   # 1 = relâché au démarrage

print(f"Appuyer sur le bouton BOOT → LED allumée {DUREE_SECONDES} secondes")
print("Appuyer Ctrl+C pour arrêter")

while True:
    etat_actuel = bouton.value()

    # Détecter le front descendant : le bouton vient d'être APPUYÉ
    # (passage de 1 à 0 — logique active bas)
    if etat_precedent == 1 and etat_actuel == 0:
        print(f"Bouton appuyé → LED allumée pour {DUREE_SECONDES} s")
        led.on()
        time.sleep(DUREE_SECONDES)   # attendre la durée configurée
        led.off()
        print("Temps écoulé → LED éteinte")

    etat_precedent = etat_actuel   # mémoriser l'état pour le prochain tour

    time.sleep(0.05)   # pause 50 ms — anti-rebond et économie de ressources

# -----------------------------------------------------------------------
# À RETENIR :
#   - Front descendant (1→0) : le bouton vient d'être appuyé
#   - Front montant  (0→1) : le bouton vient d'être relâché
#   - On mémorise "etat_precedent" pour comparer à chaque tour de boucle
#   - Cette technique s'applique à tout ce qui change d'état :
#     boutons, capteurs de présence, fins de course...
#
# VARIANTES À ESSAYER :
#   - Changer DUREE_SECONDES = 10 pour 10 secondes
#   - Faire clignoter la LED pendant les 2 dernières secondes (avertissement)
#   - Allonger la durée à chaque appui supplémentaire
# -----------------------------------------------------------------------
