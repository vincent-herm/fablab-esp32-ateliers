# Atelier 04 — Lumière automatique (LDR + LED PWM)
# Fablab Ardèche — MicroPython
#
# Une cellule photoélectrique (LDR) mesure la luminosité ambiante.
# Quand il fait sombre, la LED s'allume automatiquement.
# La luminosité de la LED est proportionnelle à l'obscurité.
#
# Matériel : ESP32, LDR + résistance 10kΩ, LED + résistance 220Ω
# Connexions :
#   LDR (pont diviseur) → GPIO34 (ADC)
#   LED                 → GPIO2  (PWM)
#   Bouton mode         → GPIO0  (PULL_UP)

from machine import Pin, ADC, PWM
import time

# --- Configuration ---
SEUIL_NUIT  = 1500   # en dessous = sombre → LED s'allume
SEUIL_JOUR  = 2500   # au dessus  = clair  → LED s'éteint (hystérésis)

# --- Initialisation ---
ldr  = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)    # plage 0–3.3V
ldr.width(ADC.WIDTH_12BIT)  # résolution 12 bits

pwm = PWM(Pin(2), freq=1000)
bp  = Pin(0, Pin.IN, Pin.PULL_UP)

# --- Modes ---
MODES = ["Auto", "Toujours ON", "Toujours OFF"]
mode  = 0
led_allumee = False

def correction_gamma(valeur_0_100):
    """Correction perceptuelle : l'œil perçoit mieux une courbe quadratique."""
    return int((valeur_0_100 / 100) ** 2 * 1023)

def luminosite_led(ldr_val):
    """Calcule la luminosité LED selon la valeur LDR (0=sombre → LED forte)."""
    if ldr_val >= SEUIL_JOUR:
        return 0
    elif ldr_val <= SEUIL_NUIT:
        return 100
    else:
        # Zone de transition : interpolation linéaire
        pct = (SEUIL_JOUR - ldr_val) / (SEUIL_JOUR - SEUIL_NUIT) * 100
        return int(pct)

# --- Boucle principale ---
print("Lumière automatique démarrée")
print(f"Seuil nuit : {SEUIL_NUIT}  |  Seuil jour : {SEUIL_JOUR}")
print("Appuie sur BOOT pour changer de mode")

t_btn = time.ticks_ms()

while True:
    now = time.ticks_ms()

    # --- Bouton : changer de mode ---
    if bp.value() == 0 and time.ticks_diff(now, t_btn) > 300:
        mode = (mode + 1) % len(MODES)
        t_btn = now
        print(f"Mode : {MODES[mode]}")
        while bp.value() == 0:   # attendre relâchement
            time.sleep_ms(20)

    # --- Lecture LDR ---
    ldr_val = ldr.read()
    tension = ldr_val * 3.3 / 4095

    # --- Calcul luminosité selon le mode ---
    if MODES[mode] == "Auto":
        pct = luminosite_led(ldr_val)
    elif MODES[mode] == "Toujours ON":
        pct = 100
    else:
        pct = 0

    duty = correction_gamma(pct)
    pwm.duty(duty)

    print(f"LDR={ldr_val} ({tension:.2f}V)  LED={pct}%  Mode={MODES[mode]}")
    time.sleep_ms(200)
