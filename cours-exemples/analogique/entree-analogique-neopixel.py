from machine import Pin, ADC
from time import sleep
from machine import Pin
from neopixel import NeoPixel

adc = ADC(Pin(35))        # cree l'objet ADC
adc.atten(ADC.ATTN_11DB)  # set 11dB input attenuation (range 0.0v - 3.6v)
adc.width(ADC.WIDTH_9BIT) # set 9 bit return values (returned range 0-511)
np = NeoPixel(Pin(26), 8)

for x in range(100):      # boucle pendant 10 s
    raw = adc.read()
    print("raw : {0:3d}, tension : {1:f}, raw/64 : {2:f}".
          format(raw, raw * 3.3 / 511, raw/64))
    for led in range(8):
        np[led]=(0, 0, 10*(raw/64 > led))  # allume 0-8 leds du neopixel
    np.write()
    sleep(.1)