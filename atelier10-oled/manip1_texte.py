from machine import Pin, I2C
from time import sleep_ms
import ssd1306

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400_000)
print("Adresses I2C trouvées :", [hex(a) for a in i2c.scan()])

oled = ssd1306.SSD1306_I2C(128, 64, i2c)   # 128 × 64 pixels

oled.fill(0)                       # tout éteindre
oled.rect(0, 0, 128, 64, 1)        # cadre autour de l'écran
oled.text("Fablab", 40, 4)         # texte, x, y
oled.text("Sud-Ardeche", 20, 18)
oled.hline(10, 32, 108, 1)         # ligne horizontale
oled.text("Compteur :", 8, 40)
oled.show()                        # envoyer l'image vers l'écran

compteur = 0
while True:
    oled.fill_rect(88, 40, 36, 8, 0)   # effacer seulement la zone du nombre
    oled.text(str(compteur), 88, 40)
    oled.show()
    compteur += 1
    sleep_ms(500)
