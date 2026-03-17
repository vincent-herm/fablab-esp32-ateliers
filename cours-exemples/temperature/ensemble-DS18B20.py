from time import time, sleep
from esp32 import Partition , ULP
from onewire import OneWire
from ds18x20 import DS18X20
from machine import Pin, ADC, DAC, PWM

ds_pin = Pin(27)                     # definie pin capteur
ds_sensor = DS18X20(OneWire(ds_pin))

def read_ds_sensor(s):               # notre fonction de mesure
  roms = ds_sensor.scan()
  ds_sensor.convert_temp()
  sleep(.5)
  if s=="INT":                       # INT : capteur interieur
      rom = bytearray(b'(\xa6d\x16\xa8\x01<\xc5') # son code ROM
  if s=="EXT":                       # EXT : capteur Exterieur
      rom = bytearray(b'(\xff\xa3\x9ed\x15\x01\xb7') # son code ROM
  temp = ds_sensor.read_temp(rom)    # on lit le capteur choisi
  return temp                        # on retourne la temperature

tempINT = read_ds_sensor("INT")
print('Capteur Interieur - sur carte  : ', tempINT, 'degres')

tempEXT = read_ds_sensor("EXT")
print('Capteur Exterieur - WaterProof : ', tempEXT, 'degres')

