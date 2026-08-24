# Test lecture / écriture RFID RC522 — MIFARE Classic 1K
# -----------------------------------------------------------------------
# Câblage ESP32 → RC522 :
#   D18 → SCK   D23 → MOSI   D19 → MISO   D5 → NSS   D22 → RST
#
# Ce programme :
#   1. Lit l'UID du badge
#   2. Lit le contenu du bloc 4 (données libres, secteur 1)
#   3. Propose d'écrire un texte dans ce bloc
#   4. Relit pour vérifier
#
# Bloc 4 = secteur 1, bloc 0 — zone libre, sans risque
# -----------------------------------------------------------------------

from machine import Pin, SPI
import time

from mfrc522 import MFRC522

spi  = SPI(1, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rfid = MFRC522(spi, gpioRst=22, gpioCs=5)

KEY  = b'\xFF\xFF\xFF\xFF\xFF\xFF'   # clé par défaut MIFARE Classic
BLOC = 4                              # secteur 1, bloc 0 — libre et safe


# =============================================================================
# FONCTIONS DE BASE
# =============================================================================

def uid_vers_str(uid):
    return ':'.join(f'{b:02X}' for b in uid)


def attendre_badge():
    """Attend un badge, le sélectionne et retourne son UID."""
    while True:
        stat, _ = rfid.request(rfid.REQIDL)
        if stat == rfid.OK:
            stat, uid = rfid.anticoll()
            if stat == rfid.OK:
                uid = bytearray(uid)
                if rfid.select_tag(uid) == rfid.OK:   # sélection obligatoire
                    return uid
        time.sleep_ms(100)


def reveiller_et_selectionner(uid):
    """Séquence complète après stop_crypto1 : request → anticoll → select.
    Utilise REQALL + 3 tentatives car la carte peut être en état incertain."""
    for _ in range(5):
        stat, _ = rfid.request(rfid.REQALL)
        if stat == rfid.OK:
            stat, _ = rfid.anticoll()
            if stat == rfid.OK:
                if rfid.select_tag(uid) == rfid.OK:
                    return True
        time.sleep_ms(80)
    return False


def authentifier(uid, bloc):
    """Authentifie le secteur — la carte doit déjà être sélectionnée."""
    trailer = (bloc // 4) * 4 + 3
    return rfid.auth(rfid.AUTHENT1A, trailer, KEY, uid) == rfid.OK


def lire_bloc(uid, bloc):
    """Lit 16 octets — la carte doit être sélectionnée au préalable."""
    if not authentifier(uid, bloc):
        rfid.stop_crypto1()
        print("  ✗ Erreur : authentification échouée (clé incorrecte ?)")
        return None

    data = rfid.read(bloc)
    rfid.stop_crypto1()

    if data is None:
        print("  ✗ Erreur : lecture échouée")
    return data


def ecrire_bloc(uid, bloc, texte):
    """Écrit un texte dans le bloc — 3 tentatives, vérification par relecture."""
    buf = bytearray(16)
    encoded = texte[:16].encode('utf-8')
    buf[:len(encoded)] = encoded

    for tentative in range(1, 4):
        print(f"  Tentative {tentative}/3...")

        if not reveiller_et_selectionner(uid):
            print("  ✗ Sélection impossible — garde le badge immobile sur le lecteur")
            time.sleep_ms(100)
            continue

        if not authentifier(uid, bloc):
            rfid.stop_crypto1()
            print("  ✗ Authentification échouée")
            time.sleep_ms(100)
            continue

        rfid.write(bloc, buf)   # driver retourne parfois ERR même si OK
        rfid.stop_crypto1()

        # Vérification par relecture
        time.sleep_ms(300)
        if not reveiller_et_selectionner(uid):
            # Écriture probablement OK mais on ne peut pas vérifier
            print("  ~ Écrit (vérification impossible — badge bougé ?)")
            return True

        data = lire_bloc(uid, bloc)
        if data and len(data) == 16:
            try:
                lu = data.decode('utf-8').rstrip('\x00')
            except:
                lu = ''
            if lu == texte[:16]:
                print(f"  ✓ Vérifié : {repr(lu)}")
                return True
            else:
                print(f"  ✗ Contenu incorrect (lu : {repr(lu)}) — nouvelle tentative")
        else:
            print("  ✗ Relecture échouée — nouvelle tentative")

        time.sleep_ms(200)

    print("  ✗ Échec après 3 tentatives — repositionne le badge et réessaie")
    return False


def afficher_bloc(data):
    """Affiche 16 octets en hex et en texte."""
    if len(data) < 16:
        print(f"  (données incomplètes : {len(data)} octet(s))")
        return
    hex_str = ' '.join(f'{b:02X}' for b in data)
    try:
        texte = data.decode('utf-8').rstrip('\x00')
    except:
        texte = '(non UTF-8)'
    print(f"  Hex  : {hex_str}")
    print(f"  Texte: {repr(texte)}")


# =============================================================================
# TEST PRINCIPAL
# =============================================================================

print("=" * 50)
print("  TEST LECTURE / ÉCRITURE RFID RC522")
print("=" * 50)
print(f"  Bloc testé : {BLOC}  (secteur {BLOC // 4})")
print()

while True:
    print("─" * 50)
    print("Présentez un badge...")
    uid = attendre_badge()
    print(f"  UID : {uid_vers_str(uid)}")
    print()

    # --- LECTURE ---
    print(f"Lecture du bloc {BLOC} :")
    data = lire_bloc(uid, BLOC)
    if data:
        afficher_bloc(data)
    print()

    # --- ÉCRITURE ---
    texte = input("Texte à écrire (max 16 car., Entrée pour passer) : ").strip()
    if texte:
        print(f"Écriture du bloc {BLOC} :")
        ecrire_bloc(uid, BLOC, texte)

    print()
    time.sleep(1)   # laisser le temps d'éloigner le badge
