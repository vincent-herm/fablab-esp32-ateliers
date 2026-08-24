# neopixel_potentiometre.py — LED défilante sur NeoPixel selon potentiomètre
# -----------------------------------------------------------------------
# Potentiomètre sur Pin 35 — ADC 9 bits (0-511)
# NeoPixel 8 LEDs sur Pin 26
#
# La LED allumée se déplace de 0 à 7 selon la position du potentiomètre.
# -----------------------------------------------------------------------

from machine import Pin, ADC
from neopixel import NeoPixel
from time import sleep_ms

p1 = ADC(Pin(35))
p1.atten(ADC.ATTN_11DB)
p1.width(ADC.WIDTH_9BIT)

np = NeoPixel(Pin(26), 8)

while True:
    val = p1.read()              # 0 à 511
    pos = val * 7 // 511         # mapping → 0 à 7

    for i in range(8):
        np[i] = (0, 30, 0) if i == pos else (0, 0, 0)
    np.write()

    sleep_ms(20)
