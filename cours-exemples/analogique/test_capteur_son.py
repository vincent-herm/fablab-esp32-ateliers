# test_capteur_son.py — Test capteur de son (sortie analogique)
# -----------------------------------------------------------------------
# Capteur    VCC → 3.3V      GND → GND
#            AO  → Pin 34    (sortie analogique brute)
#
# Résultat dans le Shell Thonny :
#   AO:258  [......................]  pic:  0
#   AO:389  [##########............]  pic:131   ← son détecté
# -----------------------------------------------------------------------

from machine import ADC, Pin
from time import sleep_ms

ao = ADC(Pin(34))
ao.atten(ADC.ATTN_11DB)
ao.width(ADC.WIDTH_9BIT)   # 0 – 511

# Ce capteur repose à 511 (max) et descend quand il détecte du son
REPOS = 511
BARS  = 24

print("=== Test capteur de son ===")
print("AO Pin 34  — silence = 511, descend avec le son")
print("Parlez, tapez des mains, soufflez...")
print()

pic = 0
compteur = 0

def lire_amplitude():
    """Échantillonne 100 fois en ~20ms et retourne le pic détecté."""
    mini = 511
    for _ in range(100):
        v = ao.read()
        if v < mini:
            mini = v
    return REPOS - mini   # 0 = silence, 511 = son maximum

while True:
    amp  = lire_amplitude()
    nb   = amp * BARS // 511
    visu = "#" * nb + "." * (BARS - nb)

    if amp > pic:
        pic = amp
    compteur += 1
    if compteur % 8 == 0:   # reset pic toutes les ~8 affichages
        pic = 0

    print(f"amp:{amp:3d}  [{visu}]  pic:{pic:3d}")
