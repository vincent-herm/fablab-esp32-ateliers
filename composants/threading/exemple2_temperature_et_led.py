# Threading — Exemple 2 : Température en continu + LED réactive
# Fablab Ardèche — ESP32 dual core
# -----------------------------------------------------------------------
# Cœur 0 (principal) : lit la température du processeur toutes les 2s
# Cœur 1 (thread)    : fait "respirer" la LED en PWM en continu
#
# Les deux tâches tournent en parallèle sans se gêner.
# La LED respire de façon fluide pendant que la température s'affiche.
#
# Rien à brancher — LED intégrée GPIO 2.
# -----------------------------------------------------------------------

from machine import Pin, PWM
from time import sleep, sleep_ms
import _thread
import esp32

led = PWM(Pin(2), freq=1000)

# --- Thread : LED qui respire en continu (cœur 1) ---
def respirer():
    """Fait monter et descendre la luminosité en boucle."""
    while True:
        # Montée
        for i in range(0, 1023, 5):
            led.duty(i)
            sleep_ms(5)
        # Descente
        for i in range(1023, 0, -5):
            led.duty(i)
            sleep_ms(5)

# Lancer le thread
_thread.start_new_thread(respirer, ())

print("LED qui respire en arrière-plan (cœur 1)")
print("Température du processeur en continu (cœur 0)")
print("Ctrl+C pour arrêter")
print()

# --- Programme principal : lecture température (cœur 0) ---
while True:
    temp_f = esp32.raw_temperature()
    temp_c = (temp_f - 32) / 1.8
    print(f"Température processeur : {temp_c:.1f} °C")
    sleep(2)

# -----------------------------------------------------------------------
# OBSERVER :
#   La LED respire de façon FLUIDE pendant que les print s'affichent.
#   Sans threading, le sleep(2) de la température bloquerait la LED.
#
# C'EST LE DUAL CORE EN ACTION :
#   Cœur 0 : print + sleep(2) → ne gêne pas la LED
#   Cœur 1 : PWM respiration → ne gêne pas les print
# -----------------------------------------------------------------------
