# Threading — Exemple 1 : Deux LEDs à des rythmes différents
# Fablab Ardèche — ESP32 dual core
# -----------------------------------------------------------------------
# L'ESP32 a DEUX cœurs de processeur. Avec le module _thread,
# on peut lancer deux tâches en parallèle, chacune sur un cœur.
#
# Ici : la LED intégrée (GPIO2) clignote toutes les 0,5 s
#        en même temps qu'une autre tâche tourne sur l'autre cœur.
#
# Sans threading, une seule boucle while True peut tourner à la fois.
# Avec threading, on en lance DEUX qui tournent en parallèle.
#
# Rien à brancher — LED intégrée GPIO 2 + bouton BOOT GPIO 0.
# -----------------------------------------------------------------------

from machine import Pin
from time import sleep
import _thread                     # module de threading MicroPython

led = Pin(2, Pin.OUT)
bouton = Pin(0, Pin.IN, Pin.PULL_UP)

# --- Tâche 1 : clignotement en arrière-plan (sur le 2e cœur) ---
def clignoter():
    """Fait clignoter la LED à 1 Hz, indéfiniment."""
    while True:
        led.value(not led.value())   # inverse l'état de la LED
        sleep(0.5)

# --- Lancer le thread (démarre sur le 2e cœur) ---
_thread.start_new_thread(clignoter, ())

print("La LED clignote en arrière-plan.")
print("Pendant ce temps, le cœur principal est libre.")
print()

# --- Tâche principale : compter les appuis sur le bouton BOOT ---
compteur = 0
while True:
    if bouton.value() == 0:          # bouton appuyé
        compteur += 1
        print(f"Appui n°{compteur}")
        sleep(0.3)                   # anti-rebond
        while bouton.value() == 0:   # attendre le relâchement
            pass

# -----------------------------------------------------------------------
# CE QUI SE PASSE :
#   Cœur 0 (principal) : compte les appuis sur le bouton BOOT
#   Cœur 1 (thread)    : fait clignoter la LED en permanence
#
#   Les deux tournent en MÊME TEMPS. La LED clignote même pendant
#   qu'on compte les appuis — impossible sans threading.
#
# À RETENIR :
#   _thread.start_new_thread(fonction, ())   # lance une fonction sur le 2e cœur
#   La fonction ne doit JAMAIS se terminer (boucle infinie)
#   Pas de return, pas de fin — sinon le thread meurt
# -----------------------------------------------------------------------
