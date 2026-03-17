from machine import Pin, ADC
from time import sleep
from machine import Pin

adc = ADC(Pin(35))        # cree l'objet ADC, pour une entree analogique
adc.atten(ADC.ATTN_11DB)  # set 11dB input attenuation (range 0.0v - 3.6v)
adc.width(ADC.WIDTH_9BIT) # set 9 bit return values (returned range 0-511)

for x in range(100):      # boucle pendant 10 s
    raw = adc.read()      # lecture de raw (entre 0 et 511)
    print(raw) 
    sleep(.1)