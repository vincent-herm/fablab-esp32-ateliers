# Exemple 1 — Afficher du texte fixe sur la matrice LED 8x32
# Fablab Ardèche — Composant : MAX7219 (1088AS)
# -----------------------------------------------------------------------
# Affiche un texte fixe sur l'afficheur 4 modules (32 colonnes x 8 lignes).
# Le texte intégré de MicroPython fait ~6 pixels de large par caractère,
# donc on peut afficher environ 5 caractères à la fois.
#
# Câblage ESP32 → MAX7219 :
#   GPIO23 (MOSI) → DIN
#   GPIO18 (SCK)  → CLK
#   GPIO5         → CS
#   5V            → VCC
#   GND           → GND
# -----------------------------------------------------------------------

from machine import Pin, SPI
import max7219

# Initialisation SPI — baudrate 10 MHz (stable sur ESP32)
spi = SPI(2, baudrate=10000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)

# 4 modules 1088AS en cascade = 32 colonnes × 8 lignes
ecran = max7219.Matrix8x8(spi, cs, 4)

# Luminosité : 0 (minimum) à 15 (maximum)
ecran.brightness(5)

# Effacer l'écran
ecran.fill(0)

# Écrire du texte à la position (x=0, y=0)
ecran.text("HELLO", 0, 0, 1)

# Afficher sur l'écran (obligatoire après chaque modification)
ecran.show()

# -----------------------------------------------------------------------
# ESSAYER DANS LE SHELL :
#   >>> ecran.fill(0)
#   >>> ecran.text("FABLAB", 0, 0, 1)
#   >>> ecran.show()
#
#   >>> ecran.brightness(15)     # luminosité max
#   >>> ecran.brightness(1)      # luminosité min
# -----------------------------------------------------------------------
