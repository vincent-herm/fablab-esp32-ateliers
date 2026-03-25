# Manipulation 07 — Lire la température interne du processeur
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# L'ESP32 intègre un capteur de température à l'intérieur même du chip.
# Il mesure la température du processeur (pas la température ambiante).
#
# À quoi ça sert ?
#   - Surveiller que le processeur ne surchauffe pas
#   - Démontrer qu'un microcontrôleur peut avoir des capteurs intégrés
#
# ATTENTION : la valeur est en degrés Fahrenheit dans MicroPython.
#             On la convertit en Celsius avec la formule : (F - 32) / 1,8
#
# Astuce de démonstration : approcher le doigt (ou un objet chaud)
# près de la puce ESP32 pendant quelques secondes → la valeur monte.
#
# Rien à brancher — capteur interne au chip.
# -----------------------------------------------------------------------

import esp32    # module spécifique à l'ESP32, contient les fonctions internes
import time     # pour les pauses

print("Température interne du processeur ESP32")
print("Approchez le doigt près de la puce pour voir la valeur monter...")
print("Appuyer Ctrl+C pour arrêter")
print()

while True:
    # Lecture de la température brute (en Fahrenheit)
    temp_fahrenheit = esp32.raw_temperature()

    # Conversion en Celsius
    temp_celsius = (temp_fahrenheit - 32) / 1.8

    # Affichage avec une décimale
    print(f"Température : {temp_celsius:.1f} °C  ({temp_fahrenheit} °F)")

    time.sleep(1)    # une mesure par seconde

# -----------------------------------------------------------------------
# À RETENIR :
#   - Le module "esp32" donne accès aux fonctions spéciales de la puce
#   - raw_temperature() retourne des degrés Fahrenheit (héritage américain)
#   - Formule de conversion : °C = (°F - 32) / 1.8
#   - f"..." = f-string : façon moderne d'insérer des variables dans du texte
#   - :.1f = formater un nombre avec 1 décimale
#
# DANS LE SHELL :
#   >>> import esp32
#   >>> esp32.raw_temperature()
#   >>> (esp32.raw_temperature() - 32) / 1.8
# -----------------------------------------------------------------------
