# Régulation PID de température — ESP32 + MOSFET + DS18B20
# Fablab Ardèche — Cours avancé
# -----------------------------------------------------------------------
# Le système chauffe une résistance de puissance via un MOSFET,
# mesure la température avec un DS18B20, et régule par PID.
#
# Câblage :
#   GPIO26 → Gate du MOSFET IRLZ44N (PWM de chauffe)
#   GPIO27 → DATA du DS18B20 (+ pull-up 4,7 kΩ vers 3.3V)
#   MOSFET : Drain → résistance de puissance → +VCC
#            Source → GND
#   DS18B20 : VCC → 3.3V, GND → GND
#
# Utilisation :
#   1. Lancer le programme
#   2. Taper la consigne dans le Shell (ex: 45)
#   3. Observer la régulation dans le Shell
#   4. Ctrl+C pour arrêter
# -----------------------------------------------------------------------

from machine import Pin, PWM
from onewire import OneWire
from ds18x20 import DS18X20
from time import sleep_ms, ticks_ms, ticks_diff

# --- Matériel ---
chauffe = PWM(Pin(26), freq=1000)    # MOSFET sur GPIO26
chauffe.duty(0)                       # éteint au démarrage

ds_pin = Pin(27)
ds = DS18X20(OneWire(ds_pin))
roms = ds.scan()
if not roms:
    print("ERREUR : aucun DS18B20 trouvé sur GPIO27")
    raise SystemExit
capteur = roms[0]
print(f"DS18B20 trouvé : {capteur}")

# --- Paramètres PID ---
# Ces valeurs sont un point de départ — à ajuster selon le système
Kp = 50.0      # gain proportionnel
Ki = 0.5       # gain intégral
Kd = 20.0      # gain dérivé

# --- Variables PID ---
consigne = 0.0          # température cible (°C)
somme_erreurs = 0.0     # intégrale des erreurs
erreur_prec = 0.0       # erreur au pas précédent
ANTI_WINDUP = 500.0     # limite de l'intégrale (évite l'emballement)


def lire_temperature():
    """Lit la température du DS18B20 (bloque ~750 ms)."""
    ds.convert_temp()
    sleep_ms(750)        # le DS18B20 a besoin de 750 ms pour convertir
    return ds.read_temp(capteur)


def calculer_pid(mesure):
    """Calcule la commande PID (0-1023) à partir de la mesure."""
    global somme_erreurs, erreur_prec

    erreur = consigne - mesure

    # Proportionnel
    P = Kp * erreur

    # Intégral (avec anti-windup)
    somme_erreurs += erreur
    somme_erreurs = max(-ANTI_WINDUP, min(ANTI_WINDUP, somme_erreurs))
    I = Ki * somme_erreurs

    # Dérivé
    D = Kd * (erreur - erreur_prec)
    erreur_prec = erreur

    # Commande totale, limitée entre 0 et 1023
    commande = P + I + D
    commande = max(0, min(1023, int(commande)))

    return commande, P, I, D, erreur


def afficher(mesure, commande, P, I, D, erreur):
    """Affiche une ligne de suivi dans le Shell."""
    pct = int(commande * 100 / 1023)
    print(f"  Consigne: {consigne:.1f}°C | Mesure: {mesure:.1f}°C | "
          f"Erreur: {erreur:+.1f} | Cmd: {pct:3d}% | "
          f"P={P:+.0f} I={I:+.0f} D={D:+.0f}")


# --- Saisie de la consigne ---
print()
print("=" * 55)
print("  RÉGULATION PID DE TEMPÉRATURE")
print("=" * 55)
print()

# Première mesure
temp = lire_temperature()
print(f"  Température actuelle : {temp:.1f} °C")
print()

try:
    consigne = float(input("  Consigne (°C) : "))
except ValueError:
    consigne = 45.0
    print(f"  Valeur invalide — consigne par défaut : {consigne} °C")

print()
print(f"  Kp={Kp}  Ki={Ki}  Kd={Kd}")
print(f"  Régulation vers {consigne} °C — Ctrl+C pour arrêter")
print("-" * 55)

# --- Boucle de régulation ---
try:
    while True:
        # Lire la température
        mesure = lire_temperature()

        # Calculer la commande PID
        commande, P, I, D, erreur = calculer_pid(mesure)

        # Appliquer la commande au MOSFET
        chauffe.duty(commande)

        # Afficher le suivi
        afficher(mesure, commande, P, I, D, erreur)

except KeyboardInterrupt:
    chauffe.duty(0)
    print()
    print("  Chauffe coupée. Régulation arrêtée.")

# -----------------------------------------------------------------------
# RÉGLAGE DES PARAMÈTRES PID :
#
# Méthode simple (essai-erreur) :
#
# 1. Commencer avec Ki=0, Kd=0, augmenter Kp
#    → Kp trop faible : monte lentement, n'atteint pas la consigne
#    → Kp correct : monte et se stabilise près de la consigne (erreur statique)
#    → Kp trop fort : oscille autour de la consigne
#
# 2. Ajouter Ki progressivement (0.1, 0.2, 0.5...)
#    → Élimine l'erreur statique (la température atteint exactement la consigne)
#    → Ki trop fort : oscillations lentes
#
# 3. Ajouter Kd progressivement (5, 10, 20...)
#    → Réduit le dépassement (overshoot)
#    → Kd trop fort : réaction nerveuse, vibrations
#
# VALEURS DE DÉPART SUGGÉRÉES :
#   Résistance 10Ω 5W + DS18B20 : Kp=50, Ki=0.5, Kd=20
#   Ajuster en observant la réponse dans le Shell.
#
# ANTI-WINDUP :
#   Si la consigne est très éloignée, l'intégrale accumule une valeur
#   énorme. Quand la température arrive enfin à la consigne, l'intégrale
#   est si grande que le système dépasse largement. L'anti-windup limite
#   la valeur de l'intégrale pour éviter ce phénomène.
# -----------------------------------------------------------------------
