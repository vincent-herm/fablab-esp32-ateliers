from machine import Pin
from onewire import OneWire
from time import sleep, sleep_ms
from ds18x20 import DS18X20

ds_pin = Pin(27)                       # definie pin capteur
ds_capteur = DS18X20(OneWire(ds_pin))  # cree l'objet ds_capteur

roms = ds_capteur.scan()               # scanne l'ensemble des capteurs
print('Found DS devices : ', roms)     # affiche les codes ROM trouves

ds_capteur.convert_temp()              # lance la lecture 
sleep_ms(500)                          # temporisation pour lecture
for x, rom in enumerate(roms) :                       
    print(" ")
    print("Capteur : ", x)             
    print("Code ROM : ", rom)          # affiche code ROM capteur
    print(ds_capteur.read_temp(rom))   # affiche la temperature
