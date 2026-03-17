from machine import Pin, ADC
from time import sleep
from machine import Pin

adc = ADC(Pin(32))        # cree l'objet ADC, pour une entree analogique
adc.atten(ADC.ATTN_11DB)  # set 11dB input attenuation (range 0.0v - 3.6v)
adc.width(ADC.WIDTH_9BIT) # set 9 bit return values (returned range 0-511)
led = Pin(23, Pin.OUT)

for x in range(100):
    tension = adc.read()* 3.3 / 512       # calcul de la tension (9 bits)
    led.value(tension < 2.0)              # allume LED si tension < 2.0
    print("Tension : ", tension)
    sleep(.1)