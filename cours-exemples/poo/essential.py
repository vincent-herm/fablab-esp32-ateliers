from machine import I2C, Pin, PWM, ADC, TouchPad
from time import sleep, sleep_ms, sleep_us, ticks_us, ticks_ms 
from math import pi, sin
from neopixel import NeoPixel
from onewire import OneWire
from ds18x20 import DS18X20

#Importation des modules pour les afficheurs OLED 
from ssd1306 import SSD1306_I2C     # module pour commander le OLED
i2c = I2C(-1, Pin(22), Pin(21))     # pin SCK et SDA du OLED
display = SSD1306_I2C(128, 64, i2c) # declaration taille ecran, pins

from sh1106 import SH1106_I2C
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
display = SH1106_I2C(128, 64, i2c, Pin(16), 0x3c)
display.sleep(False)

ds_pin = Pin(27)                       # definie pin DS18B20
ds_capteur = DS18X20(OneWire(ds_pin))  # cree l'objet ds_capteur

led_bleue = Pin(2, Pin.OUT)
led_verte = Pin(18, Pin.OUT)
led_jaune = Pin(19, Pin.OUT)
led_rouge = Pin(23, Pin.OUT)

tp1 = TouchPad(Pin(15))
tp2 = TouchPad(Pin(4))

bpA = Pin(25, Pin.IN)
bpB = Pin(34, Pin.IN)
bpC = Pin(39, Pin.IN)
bpD = Pin(36, Pin.IN)

p1 = ADC(Pin(35))        # cree l'objet ADC   # CHANGEMENT !
p1.atten(ADC.ATTN_11DB)  # set 11dB input attenuation (range 0.0v - 3.6v)
p1.width(ADC.WIDTH_9BIT) # set 9 bit return values (returned range 0-511)

p2 = ADC(Pin(33))        # cree l'objet ADC
p2.atten(ADC.ATTN_11DB)  # set 11dB input attenuation (range 0.0v - 3.6v)
p2.width(ADC.WIDTH_9BIT) # set 9 bit return values (returned range 0-511)

ldr = ADC(Pin(32))        # cree l'objet ADC
ldr.atten(ADC.ATTN_11DB)  # set 11dB input attenuation (range 0.0v - 3.6v)
ldr.width(ADC.WIDTH_9BIT) # set 9 bit return values (returned range 0-511)

n = 8                          # nombre de pixels
p = 26                         # pin de commande du neopixel
np = NeoPixel(Pin(p), n)       # creation de l'instance np

buzzer = PWM(Pin(5))
buzzer.deinit()      # rapport cyclique a 30 sur 1023, soit environ 3 %

global liste_freq
liste_freq = [int(2**(x/12)*880) for x in range (0,13)]  # 13 notes
if __name__ == "__main__":
    print(liste_freq)

def  adaptEchelle(e, e1, e2, s1, s2) :     
    s = (e - e1) * (s2 - s1) / (e2 - e1) + s1  # e : entree , s : sortie
    return s                                   # renvoie la valeur sortie

def attend_appui() :
  while bpA.value() == True : pass ; sleep(.02) # attend relach. poussoir
  while bpA.value() == False : pass ; sleep(.02)  # attend appui poussoir
    
def attend_touch() :
  while tp1.read() < 350 : pass ; sleep(.02) # attend relach. poussoir
  while tp1.read() > 350 : pass ; sleep(.02)  # attend appui poussoir
    
def synchro_us(delai) :
    global boucle_us, top
    if boucle_us == 0 :
        top = ticks_us()
    tip = ticks_us()
    boucle_us = boucle_us + 1
    delta = tip - top
    #print(delta)
    sleep_us((delai * boucle_us - delta))

def synchro_ms(delai) :
    global boucle_ms, top
    if boucle_ms == 0 :
        top = ticks_ms()
    tip = ticks_ms()
    boucle_ms = boucle_ms + 1
    delta = tip - top
    attente = delai * boucle_ms - delta
    sleep_ms(attente)
    #print("delta : ", delta, " - attente: ", attente)

boucle_ms = 0






