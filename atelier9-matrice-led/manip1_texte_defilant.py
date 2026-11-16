from machine import Pin, SPI
from time import sleep_ms
from max7219 import Matrix8x8

# --- Personnalise ton message ici ---
message = "FABLAB SUD-ARDECHE "
# ------------------------------------

spi = SPI(2, baudrate=10_000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
cs  = Pin(5, Pin.OUT)

display = Matrix8x8(spi, cs, 4)  # 4 matrices en cascade
display.brightness(3)            # 0 = minimum, 15 = maximum

largeur_msg = len(message) * 8  # chaque caractère = 8 pixels

while True:
    for x in range(32, -largeur_msg, -1):
        display.fill(0)
        display.text(message, x, 0, 1)
        display.show()
        sleep_ms(50)
