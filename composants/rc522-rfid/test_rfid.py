# Test rapide — Lecteur RFID RC522 (Joy-it) sur ESP32
# -----------------------------------------------------------------------
# Lit l'UID des badges présentés devant le lecteur et l'affiche.
# Permet de vérifier que le câblage fonctionne et de découvrir
# les identifiants de vos badges.
#
# Câblage ESP32 → RC522 :
#   D18  → SCK         D23  → MOSI       D19  → MISO
#   D5   → SDA (CS)    D22  → RST
#   3.3V → 3.3V        GND  → GND
#
#   ⚠ JAMAIS brancher le RC522 en 5V — il grille !
#
# Installation de la bibliothèque (une seule fois) :
#   Dans Thonny → Outils → Gérer les paquets → chercher "mfrc522" → Installer
#   Ou dans le Shell : import mip; mip.install("mfrc522")
# -----------------------------------------------------------------------

from machine import Pin, SPI
import time

# Importer la bibliothèque RFID
try:
    from mfrc522 import MFRC522
except ImportError:
    print("Bibliothèque mfrc522 non installée !")
    print("Dans Thonny : Outils → Gérer les paquets → mfrc522")
    raise SystemExit

# Initialisation SPI + lecteur RFID
spi  = SPI(1, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rfid = MFRC522(spi, gpioRst=22, gpioCs=5)

print("Lecteur RFID RC522 prêt")
print("Présentez un badge devant le lecteur...")
print("Ctrl+C pour arrêter")
print()

badges_vus = set()

while True:
    # Chercher un badge à proximité
    stat, tag_type = rfid.request(rfid.REQIDL)

    if stat == rfid.OK:
        # Un badge est détecté — lire son UID (identifiant unique)
        stat, uid = rfid.anticoll()

        if stat == rfid.OK:
            # Convertir l'UID en texte lisible : "AA:BB:CC:DD"
            uid_str = ':'.join(f'{b:02X}' for b in uid)

            if uid_str not in badges_vus:
                badges_vus.add(uid_str)
                print(f"Badge détecté : {uid_str}")
            else:
                print(f"  (déjà vu)    : {uid_str}")

    time.sleep_ms(200)

# -----------------------------------------------------------------------
# DANS LE SHELL après Ctrl+C :
#   >>> rfid.request(rfid.REQIDL)     # chercher un badge
#   >>> rfid.anticoll()                # lire l'UID
#
# CHAQUE BADGE A UN UID UNIQUE (4 octets en hexadécimal).
# C'est ce qui permet de distinguer les personnes :
#   "DE:AD:BE:EF" → Vincent
#   "CA:FE:BA:BE" → Marie
# -----------------------------------------------------------------------
