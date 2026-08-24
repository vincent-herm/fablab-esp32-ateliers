# oled_son.py — OLED 1.3" + capteur de son
# -----------------------------------------------------------------------
# Pins : SCL→22  SDA→21  AO son→34  bpA→25 (changer mode)
#
# Mode 1 : VU-mètre    — 16 barres verticales réactives avec pic tombant
# Mode 2 : Oscilloscope — courbe défilante de l'enveloppe sonore
# -----------------------------------------------------------------------

from machine import I2C, Pin, ADC
from sh1106 import SH1106_I2C
from time import sleep_ms

i2c     = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
display = SH1106_I2C(128, 64, i2c)

ao = ADC(Pin(34))
ao.atten(ADC.ATTN_11DB)
ao.width(ADC.WIDTH_9BIT)   # 0–511 — silence ≈ 511

bpA = Pin(25, Pin.IN)

def lire_amplitude():
    """100 lectures rapides → amplitude crête (0=silence  511=fort)"""
    mini = 511
    for _ in range(100):
        v = ao.read()
        if v < mini:
            mini = v
    return 511 - mini


# =============================================================================
# MODE 1 — VU-mètre  (16 barres, pics tombants)
# =============================================================================

def vu_metre():
    N     = 16
    MAX_H = 50
    BASE  = 63

    # Chaque barre a un lissage légèrement différent :
    # barres gauche = réponse rapide, droite = tient plus longtemps
    coeffs  = [0.45 - i * 0.015 for i in range(N)]   # 0.45 → 0.23
    lissage = [0.0] * N
    peaks   = [0]   * N

    while not bpA.value():
        amp = lire_amplitude()   # 0–511

        display.fill(0)
        display.text("VU-metre", 24, 0, 1)

        for i in range(N):
            target     = amp / 511.0 * MAX_H
            lissage[i] += (target - lissage[i]) * coeffs[i]
            h = max(1, int(lissage[i]))
            x = i * 8

            display.fill_rect(x, BASE - h, 7, h, 1)

            # Pic tombant doucement
            if h + 1 > peaks[i]:
                peaks[i] = h + 1
            else:
                peaks[i] = max(0, peaks[i] - 1)
            if peaks[i] > 2:
                display.fill_rect(x, BASE - peaks[i], 7, 2, 1)

        display.show()

    while bpA.value():
        sleep_ms(10)


# =============================================================================
# MODE 2 — Oscilloscope défilant (historique 128 points)
# =============================================================================

def oscilloscope():
    buf = bytearray(128)   # chaque octet = amplitude 0–50
    ptr = 0

    while not bpA.value():
        amp      = lire_amplitude()
        buf[ptr] = amp * 50 // 511
        ptr      = (ptr + 1) % 128

        display.fill(0)
        display.text("OSC", 0, 0, 1)
        display.text(str(amp), 96, 0, 1)

        # Ligne de base pointillée
        for x in range(0, 128, 6):
            display.pixel(x, 62, 1)

        # Courbe défilante
        for x in range(127):
            y1 = 62 - int(buf[(ptr + x)     % 128])
            y2 = 62 - int(buf[(ptr + x + 1) % 128])
            display.line(x, y1, x + 1, y2, 1)

        display.show()

    while bpA.value():
        sleep_ms(10)


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

modes = [vu_metre, oscilloscope]
noms  = ["VU-metre", "Oscilloscope"]
idx   = 0

print("=== OLED + Capteur de son ===")
print("bpA Pin 25 — changer de mode")

while True:
    print(f"-> {noms[idx]}")
    modes[idx]()
    idx = (idx + 1) % len(modes)
