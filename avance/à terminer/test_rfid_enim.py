# Test rapide — Lecteur RFID RC522 sur carte ENIM (nouveau câblage)
# -----------------------------------------------------------------------
# Lit l'UID des badges présentés devant le lecteur et l'affiche.
# Permet de vérifier que le câblage fonctionne et de découvrir
# les identifiants de vos badges.
#
# Câblage RC522 → ESP32 :
#   Pin 18 → SCK        Pin 23 → MOSI      Pin 19 → MISO
#   Pin  5 → NSS (CS)   Pin 22 → RST
#   3.3V   → 3.3V       GND    → GND
#
#   ⚠ JAMAIS brancher le RC522 en 5V — il grille !
# -----------------------------------------------------------------------

from machine import Pin, SPI
import time

try:
    from mfrc522 import MFRC522
except ImportError:
    print("Fichier mfrc522.py manquant — copier sur l'ESP32 via Thonny")
    raise SystemExit

# SPI1 (HSPI) avec le nouveau câblage carte ENIM
spi  = SPI(1, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rfid = MFRC522(spi, gpioRst=22, gpioCs=5)

print("Lecteur RFID RC522 prêt")
print("Présentez un badge devant le lecteur...")
print("Ctrl+C pour arrêter")
print()

badges_vus = set()

while True:
    stat, tag_type = rfid.request(rfid.REQIDL)

    if stat == rfid.OK:
        stat, uid = rfid.anticoll()

        if stat == rfid.OK:
            uid_str = ':'.join(f'{b:02X}' for b in uid)

            if uid_str not in badges_vus:
                badges_vus.add(uid_str)
                print(f"Badge détecté : {uid_str}  (nouveau)")
            else:
                print(f"Badge détecté : {uid_str}  (déjà vu)")

    time.sleep_ms(200)
