# Test rapide — Matrice LED MAX7219 (1088AS) sur ESP32
# -----------------------------------------------------------------------
# Câblage (côté bas de l'ESP32, de 3V3 à D23) :
#
#   MAX7219     ESP32
#   -------     -----
#   VCC    →    5V (VIN)  (ne fonctionne PAS en 3.3V)
#   GND    →    GND
#   DIN    →    D23    (GPIO23 = MOSI)
#   CLK    →    D18    (GPIO18 = SCK)
#   CS     →    D5     (GPIO5)
#
# ATTENTION : brancher sur le connecteur DIN (pas DOUT) du module !
# Lancer ce fichier dans Thonny → le texte "HELLO" doit apparaître.
# Ensuite taper les commandes dans le Shell pour jouer avec.
# -----------------------------------------------------------------------

from machine import Pin, SPI
import max7219
import time

# --- Initialisation ---
spi = SPI(2, baudrate=10000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)

# 4 modules en cascade = 32 x 8 pixels
ecran = max7219.Matrix8x8(spi, cs, 4)
ecran.brightness(3)   # luminosité basse (3V3), monter si alimenté en 5V

# --- Test 1 : texte fixe ---
print("Test 1 : texte HELLO")
ecran.fill(0)
ecran.text("HELLO", 0, 0, 1)
ecran.show()
time.sleep(2)

# --- Test 2 : tous les pixels allumés ---
print("Test 2 : tous les pixels")
ecran.fill(1)
ecran.show()
time.sleep(1)

# --- Test 3 : tous éteints ---
ecran.fill(0)
ecran.show()
time.sleep(0.5)

# --- Test 4 : texte défilant ---
print("Test 3 : texte défilant")
texte = "Fablab Polinno - Joyeuse"
largeur = len(texte) * 8
for x in range(32, -largeur, -1):
    ecran.fill(0)
    ecran.text(texte, x, 0, 1)
    ecran.show()
    time.sleep_ms(60)

# --- Fin ---
ecran.fill(0)
ecran.text("OK :)", 4, 0, 1)
ecran.show()
print("Test terminé !")

# -----------------------------------------------------------------------
# COMMANDES À TAPER DANS LE SHELL :
#
#   ecran.fill(0)                    # tout éteindre
#   ecran.text("FABLAB", 0, 0, 1)   # écrire du texte
#   ecran.show()                     # afficher
#
#   ecran.pixel(0, 0, 1)            # allumer un pixel
#   ecran.line(0, 0, 31, 7, 1)      # tracer une diagonale
#   ecran.rect(2, 1, 10, 6, 1)      # dessiner un rectangle
#   ecran.show()
#
#   ecran.brightness(15)             # luminosité max
#   ecran.brightness(1)              # luminosité min
# -----------------------------------------------------------------------
