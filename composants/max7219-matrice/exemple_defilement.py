# Exemple 2 — Texte défilant sur la matrice LED 8x32
# Fablab Ardèche — Composant : MAX7219 (1088AS)
# -----------------------------------------------------------------------
# Le texte entre par la droite et sort par la gauche, comme un bandeau
# d'information dans une gare ou un magasin.
#
# Câblage ESP32 → MAX7219 :
#   D23  → DIN       D18  → CLK       D5   → CS
#   5V   → VCC       GND  → GND
#
# ATTENTION : bien brancher sur le connecteur DIN (pas DOUT)
# -----------------------------------------------------------------------

from machine import Pin, SPI
import max7219
import time

# Initialisation SPI
spi = SPI(2, baudrate=10000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)

# 4 modules 1088AS en cascade = 32 colonnes × 8 lignes
ecran = max7219.Matrix8x8(spi, cs, 4)
ecran.brightness(5)


def defiler(texte, vitesse_ms=60):
    """Fait défiler un texte de droite à gauche.

    texte      : le message à afficher
    vitesse_ms : pause entre chaque déplacement (plus petit = plus rapide)

    Le texte fait environ 8 pixels par caractère.
    Sur un écran de 32 colonnes, on voit ~4 caractères à la fois.
    """
    largeur_texte = len(texte) * 8

    # Le texte part de x=32 (hors écran à droite)
    # et va jusqu'à x=-largeur_texte (sorti par la gauche)
    for x in range(32, -largeur_texte, -1):
        ecran.fill(0)
        ecran.text(texte, x, 0, 1)
        ecran.show()
        time.sleep_ms(vitesse_ms)


# --- Programme principal ---
print("Texte défilant — Ctrl+C pour arrêter")

while True:
    defiler("Fablab Polinno - Joyeuse - Ardeche")
    time.sleep_ms(500)    # pause entre deux passages

# -----------------------------------------------------------------------
# VARIANTES À ESSAYER :
#   defiler("Hello World!", 40)          # rapide
#   defiler("TEMPERATURE : 22.5 C", 100) # lent
#   defiler("A B C D E F G", 80)         # espaces visibles
# -----------------------------------------------------------------------
