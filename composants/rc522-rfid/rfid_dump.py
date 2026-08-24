# rfid_dump.py — Lecture complète d'un badge MIFARE Classic 1K
# -----------------------------------------------------------------------
# Lit tous les blocs accessibles et affiche leur contenu.
# Permet de savoir ce que le système d'accès stocke sur la carte.
#
# Câblage : D18→SCK  D23→MOSI  D19→MISO  D5→NSS  D22→RST
# -----------------------------------------------------------------------

from machine import Pin, SPI
import time

from mfrc522 import MFRC522

spi  = SPI(1, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rfid = MFRC522(spi, gpioRst=22, gpioCs=5)

KEY = b'\xFF\xFF\xFF\xFF\xFF\xFF'   # clé par défaut


def uid_vers_str(uid):
    return ':'.join(f'{b:02X}' for b in uid)


def attendre_badge():
    while True:
        stat, _ = rfid.request(rfid.REQIDL)
        if stat == rfid.OK:
            stat, uid = rfid.anticoll()
            if stat == rfid.OK:
                uid = bytearray(uid)
                if rfid.select_tag(uid) == rfid.OK:
                    return uid
        time.sleep_ms(100)


def lire_secteur(uid, secteur):
    """Lit les 3 blocs de données d'un secteur (pas le trailer)."""
    trailer = secteur * 4 + 3
    if rfid.auth(rfid.AUTHENT1A, trailer, KEY, uid) != rfid.OK:
        rfid.stop_crypto1()
        return None   # clé incorrecte ou secteur protégé

    blocs = []
    for b in range(secteur * 4, secteur * 4 + 3):   # blocs 0-2 du secteur
        data = rfid.read(b)
        blocs.append(data)

    rfid.stop_crypto1()
    return blocs


def reveiller(uid):
    for _ in range(3):
        stat, _ = rfid.request(rfid.REQALL)
        if stat == rfid.OK:
            stat, _ = rfid.anticoll()
            if stat == rfid.OK:
                if rfid.select_tag(uid) == rfid.OK:
                    return True
        time.sleep_ms(50)
    return False


def afficher_bloc(num, data):
    if data is None or len(data) < 16:
        print(f"  Bloc {num:2d} : (erreur lecture)")
        return False

    hex_str = ' '.join(f'{b:02X}' for b in data)
    try:
        txt = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
    except:
        txt = '.' * 16

    vide = all(b == 0 for b in data)
    tag = " ← VIDE" if vide else ""
    print(f"  Bloc {num:2d} : {hex_str}  |{txt}|{tag}")
    return not vide


# =============================================================================
# PROGRAMME PRINCIPAL
# =============================================================================

print("=" * 60)
print("  DUMP COMPLET — MIFARE Classic 1K")
print("=" * 60)
print()
print("Présentez le badge à lire...")
print()

uid = attendre_badge()
print(f"UID : {uid_vers_str(uid)}")
print()

blocs_non_vides = 0
secteurs_proteges = 0

for secteur in range(16):
    print(f"Secteur {secteur:2d} (blocs {secteur*4}-{secteur*4+3}) :")

    if secteur > 0:   # secteur 0 déjà authentifié par attendre_badge
        if not reveiller(uid):
            print("  (badge éloigné — réessaie)")
            break

    blocs = lire_secteur(uid, secteur)

    if blocs is None:
        print("  (secteur protégé — clé non standard)")
        secteurs_proteges += 1
    else:
        for i, data in enumerate(blocs):
            num_bloc = secteur * 4 + i
            if afficher_bloc(num_bloc, data):
                blocs_non_vides += 1
        print(f"  Bloc {secteur*4+3:2d} : [trailer — clés + droits d'accès]")

    time.sleep_ms(50)

print()
print("=" * 60)
print(f"Blocs non vides    : {blocs_non_vides}")
print(f"Secteurs protégés  : {secteurs_proteges}")
print()

if blocs_non_vides == 0 and secteurs_proteges == 0:
    print("→ Tous les blocs sont vides.")
    print("  Le système vérifie UNIQUEMENT l'UID.")
    print("  Il faut une carte magic UID-writable pour cloner.")
elif secteurs_proteges > 0:
    print("→ Certains secteurs ont une clé personnalisée.")
    print("  Le système stocke probablement des données sécurisées.")
    print("  Clonage plus complexe — carte magic + reverse engineering.")
else:
    print("→ Des données sont stockées dans les blocs.")
    print("  Le système utilise l'UID ET ces données.")
    print("  Il faut une carte magic + copier ces blocs.")
print("=" * 60)
