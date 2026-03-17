from machine import I2C, Pin
from time import sleep
from math import pi, sin              # import de pi et sin
from adapt import adaptEchelle        # notre fonction pour l'affichage
OLED = 1                              # 1 : 1.3 pouces, 0 : 0.96 pouces

# choix de la bibliotheque en fonction du type d'ecran OLED
if OLED == 0 :                             
    from ssd1306 import SSD1306_I2C     # module pour commander le OLED
    i2c = I2C(-1, Pin(22), Pin(21))     # pin SCK et SDA du OLED
    display = SSD1306_I2C(128, 64, i2c) # declaration taille ecran, pins
else :
    from sh1106 import SH1106_I2C
    i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
    display = SH1106_I2C(128, 64, i2c, Pin(16), 0x3c)
    display.sleep(False)

bp = Pin(25, Pin.IN)                   # poussoir sur pin 25 pour passer

# fonction pour attendre l'appui+relach. pour passer au graphique suivant
def attend_appui():
    while bp.value() == False : pass ; sleep(.02) # attend appui poussoir
    while bp.value() == True : pass ; sleep(.02)  # attend le relachement

display.fill(0)                  # Remplit l'afficheur avec 0 -> OFF
display.show()                   # Mise a jour de l'affichage (envoie)

for x in range (128) :           # 128 points car c'est la taille du OLED
    alpha = x / 128 * 2 * pi     # alpha va de 0 a 2*pi en 128 points
    y = sin(alpha)               # y va de -1 a 1
    s = int(adaptEchelle(y, -1, 1, 60, 4)) # s va de 60 a 4 
    display.pixel(x, s, 1)  
display.show() ; attend_appui()  # on affiche d'un coup les 128 points

for x in range (128) :
    alpha = x / 128 * 4 * pi     # alpha de 0 a 4*pi, soit 2 periodes
    y = sin(alpha)
    s = int(adaptEchelle(y, -1, 1, 60, 4))
    display.pixel(x, s, 1)  
display.show() ; attend_appui()

display.fill(0)
for t in range(240):             # t prend 240 valeurs
    alpha = t / 240 * 2 * pi     # alpha va de 0 a 2.pi en 240 valeurs
    x = sin(alpha * 2)
    y = sin(alpha * 3)
    sx = int(adaptEchelle(x, -1, 1, 2, 125)) # sx va de 2 a 125
    sy = int(adaptEchelle(y, -1, 1, 60, 4)) # sy va de 60 a 4
    display.pixel(sx, sy, 1)
display.show() ; attend_appui()

display.fill(0)
display.text("C'est fini !", 1, 10, 1)
display.show() 
