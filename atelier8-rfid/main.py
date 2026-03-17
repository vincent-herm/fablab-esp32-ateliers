# Atelier 08 — Badge RFID (RC522)
# Fablab Ardèche — MicroPython
#
# Un lecteur RFID RC522 identifie les badges.
# Les badges autorisés allument la LED verte (accès accordé).
# Les badges inconnus déclenchent une alarme (LED rouge + buzzer).
#
# Avant de tester : lance le script enrolement() une fois
# pour lire les UIDs de tes badges et les mettre dans BADGES_AUTORISES.
#
# Matériel : ESP32, module RC522, 2 LEDs, buzzer
# Connexions :
#   RC522 SCK  → GPIO18
#   RC522 MOSI → GPIO23
#   RC522 MISO → GPIO19
#   RC522 SDA  → GPIO5  (Chip Select)
#   RC522 RST  → GPIO22
#   RC522 3.3V → 3.3V   (JAMAIS 5V !)
#   LED verte  → GPIO2  (+ résistance 220Ω)
#   LED rouge  → GPIO4  (+ résistance 220Ω)
#   Buzzer     → GPIO15

from machine import Pin, SPI, PWM
import time

# --- Badges autorisés ---
# Remplace ces UIDs par ceux de tes propres badges
# (utilise la fonction enrolement() ci-dessous pour les lire)
BADGES_AUTORISES = {
    # 'AA:BB:CC:DD': 'Prénom',
    # 'EE:FF:00:11': 'Autre personne',
}

# --- Initialisation ---
led_v = Pin(2,  Pin.OUT)
led_r = Pin(4,  Pin.OUT)
buz   = PWM(Pin(15))
buz.duty(0)

def bip(freq=1000, duree=100, nb=1):
    for _ in range(nb):
        buz.freq(freq)
        buz.duty(300)
        time.sleep_ms(duree)
        buz.duty(0)
        time.sleep_ms(60)

def acces_accorde(nom):
    print(f"✓ Accès accordé : {nom}")
    led_v.on()
    bip(1800, 120, 2)
    time.sleep_ms(1500)
    led_v.off()

def acces_refuse(uid_str):
    print(f"✗ Accès refusé  : {uid_str}")
    for _ in range(3):
        led_r.on()
        bip(400, 200)
        led_r.off()
        time.sleep_ms(100)

def uid_vers_str(uid):
    return ':'.join(f'{b:02X}' for b in uid)

# --- Lecture RFID ---
try:
    from mfrc522 import MFRC522
    spi  = SPI(1, baudrate=1_000_000,
               sck=Pin(18), mosi=Pin(23), miso=Pin(19))
    rfid = MFRC522(spi, gpioRst=22, gpioCs=5)
    rfid_ok = True
except ImportError:
    print("⚠ Module mfrc522 non installé.")
    print("  Lance : mpremote mip install mfrc522")
    rfid_ok = False

def enrolement():
    """Lance ce mode pour lire les UIDs de tes badges."""
    print("\n=== MODE ENRÔLEMENT ===")
    print("Présente tes badges un par un devant le lecteur.")
    print("Ctrl+C pour quitter.\n")
    vus = set()
    while True:
        stat, _ = rfid.request(rfid.REQIDL)
        if stat == rfid.OK:
            stat, uid = rfid.anticoll()
            if stat == rfid.OK:
                uid_str = uid_vers_str(uid)
                if uid_str not in vus:
                    vus.add(uid_str)
                    print(f"  Badge détecté : '{uid_str}'")
                    print(f"  → Ajoute dans BADGES_AUTORISES :")
                    print(f"    '{uid_str}': 'Prénom',\n")
                    bip(1200, 80)
        time.sleep_ms(200)

# --- Boucle principale ---
if not rfid_ok:
    print("Arrêt — installe le module mfrc522 d'abord.")
else:
    # Décommenter la ligne suivante pour lire les UIDs de tes badges :
    # enrolement()

    print("Lecteur RFID prêt.")
    if not BADGES_AUTORISES:
        print("⚠ Aucun badge enregistré — tous les badges seront refusés.")
        print("  Lance enrolement() pour enregistrer des badges.")

    # Clignotement de veille
    t0 = time.ticks_ms()
    while True:
        now = time.ticks_ms()
        led_v.value((now // 1000) % 2)  # clignote 1 fois par seconde

        stat, _ = rfid.request(rfid.REQIDL)
        if stat == rfid.OK:
            stat, uid = rfid.anticoll()
            if stat == rfid.OK:
                led_v.off()
                uid_str = uid_vers_str(uid)
                if uid_str in BADGES_AUTORISES:
                    acces_accorde(BADGES_AUTORISES[uid_str])
                else:
                    acces_refuse(uid_str)

        time.sleep_ms(100)
