from machine import Pin, SPI, TouchPad
from time import sleep_ms
from max7219 import Matrix8x8

spi = SPI(2, baudrate=10_000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
cs  = Pin(5, Pin.OUT)
display = Matrix8x8(spi, cs, 4)
display.brightness(3)

touch_plus  = TouchPad(Pin(4))   # D4  → incrément
touch_moins = TouchPad(Pin(15))  # D15 → décrément
SEUIL = 200  # valeur en dessous = touché (mesure : repos ~550, touché ~80)

def afficher(n):
    display.fill(0)
    txt = str(n)
    x = (32 - len(txt) * 8) // 2  # centré
    display.text(txt, x, 0, 1)
    display.show()

compteur = 0
afficher(compteur)

while True:
    if touch_plus.read() < SEUIL:
        compteur += 1
        afficher(compteur)
        while touch_plus.read() < SEUIL:   # attendre le relâcher
            sleep_ms(10)
        sleep_ms(50)
    elif touch_moins.read() < SEUIL:
        compteur -= 1
        afficher(compteur)
        while touch_moins.read() < SEUIL:
            sleep_ms(10)
        sleep_ms(50)
    sleep_ms(20)
