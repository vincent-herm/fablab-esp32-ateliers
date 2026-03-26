# Exemple 3 — Animations sur la matrice LED 8x32
# Fablab Ardèche — Composant : MAX7219 (1088AS)
# -----------------------------------------------------------------------
# Plusieurs mini-animations pour découvrir les possibilités de l'afficheur :
#   1. Remplissage pixel par pixel
#   2. Lignes qui balaient l'écran
#   3. Rectangle qui grandit
#   4. Compteur (0 → 99)
#   5. Barre de progression
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

# Initialisation
spi = SPI(2, baudrate=10000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)
ecran = max7219.Matrix8x8(spi, cs, 4)
ecran.brightness(5)


# === Animation 1 : remplissage pixel par pixel ===
print("Animation 1 : remplissage")
ecran.fill(0)
for x in range(32):
    for y in range(8):
        ecran.pixel(x, y, 1)
        ecran.show()
        time.sleep_ms(10)
time.sleep(1)


# === Animation 2 : ligne verticale qui balaie l'écran ===
print("Animation 2 : balayage")
for x in range(32):
    ecran.fill(0)
    ecran.vline(x, 0, 8, 1)       # ligne verticale en x, hauteur 8
    ecran.show()
    time.sleep_ms(40)
time.sleep(0.5)


# === Animation 3 : rectangle qui grandit depuis le centre ===
print("Animation 3 : rectangle")
for taille in range(1, 17):
    ecran.fill(0)
    x = 16 - taille                # centré horizontalement
    y = max(0, 4 - taille // 2)    # centré verticalement
    w = taille * 2
    h = min(8, taille)
    ecran.rect(x, y, w, h, 1)
    ecran.show()
    time.sleep_ms(100)
time.sleep(1)


# === Animation 4 : compteur de 0 à 99 ===
print("Animation 4 : compteur")
for i in range(100):
    ecran.fill(0)
    ecran.text(str(i), 8, 0, 1)   # centré (8 pixels depuis la gauche)
    ecran.show()
    time.sleep_ms(50)
time.sleep(1)


# === Animation 5 : barre de progression ===
print("Animation 5 : barre de progression")
for pct in range(101):
    ecran.fill(0)
    # Barre : largeur proportionnelle au pourcentage
    largeur = int(pct * 30 / 100)
    ecran.fill_rect(1, 2, largeur, 4, 1)   # barre pleine
    ecran.rect(0, 1, 32, 6, 1)             # cadre extérieur
    ecran.show()
    time.sleep_ms(30)
time.sleep(1)


# === Fin ===
ecran.fill(0)
ecran.text("FIN", 8, 0, 1)
ecran.show()
print("Animations terminées !")

# -----------------------------------------------------------------------
# MÉTHODES DISPONIBLES (héritées de framebuf) :
#
#   ecran.pixel(x, y, 1)              # allumer un pixel
#   ecran.hline(x, y, largeur, 1)     # ligne horizontale
#   ecran.vline(x, y, hauteur, 1)     # ligne verticale
#   ecran.line(x1, y1, x2, y2, 1)    # ligne quelconque
#   ecran.rect(x, y, w, h, 1)        # rectangle vide
#   ecran.fill_rect(x, y, w, h, 1)   # rectangle plein
#   ecran.text("ABC", x, y, 1)       # texte (~8px par caractère)
#   ecran.scroll(dx, dy)              # décaler tout le contenu
#   ecran.fill(0)                     # tout effacer
#   ecran.fill(1)                     # tout allumer
#   ecran.show()                      # afficher (obligatoire)
#   ecran.brightness(0..15)           # luminosité
# -----------------------------------------------------------------------
