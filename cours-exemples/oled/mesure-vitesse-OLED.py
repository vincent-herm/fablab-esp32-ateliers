##############   mesure vitesse chute bille   ################
from machine import Pin, I2C
from time import sleep, sleep_us, sleep_ms, ticks_ms, ticks_us

# choix de la bibliotheque en fonction du type d'ecran OLED
from ssd1306 import SSD1306_I2C     # module pour commander le OLED
i2c = I2C(-1, Pin(22), Pin(21))     # pin SCK et SDA du OLED
display = SSD1306_I2C(128, 64, i2c) # declaration taille ecran, pins

from sh1106 import SH1106_I2C
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
display = SH1106_I2C(128, 64, i2c, Pin(16), 0x3c)
display.sleep(False)

display.fill(0)                  # Remplit l'afficheur avec 0 -> OFF
display.show()                   # Mise a jour de l'affichage (envoie)

relais = Pin(2, Pin.OUT)
capteur1 = Pin(25, Pin.IN)
capteur2 = Pin(34, Pin.IN)
dcy = Pin(36, Pin.IN)

relais.value(1)        # commande relais pour maintien bille

display.text("Appuyer sur DCY ...", 1, 0, 1) 
display.show() ;

# attente de l'appui sur le poussoir DCY
while not dcy.value():  # attente a l'etat bas
    pass
relais.value(0)         # lacher de la bille par ouverture relais

display.fill(0)
display.text("Attente C1...", 1, 0, 1) 
display.show() ;

# attente du passage devant le capteur 1
while not capteur1.value():  # attente a l'etat bas
    sleep_ms(1)
start = ticks_ms()      # start sur front montant 1

display.text("C1 OK", 20, 10, 1) 
display.text("Attente C2...", 1, 20, 1) 
display.show() ;

# attente du passage devant le capteur 2
while not capteur2.value():  # attente a l'etat bas
    sleep_ms(1)     
stop = ticks_ms()       # stop sur front montant 2
display.text("C2 OK", 20, 30, 1) 
delta = stop - start   
display.text("Temps C1-C2 : ", 1, 40, 1)
display.text(str(delta/1000)+ "s", 10, 50, 1)
display.show()

    


