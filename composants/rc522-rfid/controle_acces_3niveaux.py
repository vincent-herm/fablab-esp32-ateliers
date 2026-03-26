# Contrôle d'accès RFID — 3 niveaux
# Fablab Ardèche — RC522 + ESP32
# -----------------------------------------------------------------------
# Deux modes :
#   1. PROGRAMMATION : enregistrer les badges avec Nom, Prénom et niveau
#   2. PRODUCTION : scanner les badges et autoriser ou refuser l'accès
#
# Niveaux d'accès :
#   1 = Visiteur   (accès basique)
#   2 = Membre     (accès intermédiaire)
#   3 = Admin      (accès total)
#
# Les badges sont sauvegardés dans badges.json sur l'ESP32.
# Ils persistent après un redémarrage.
#
# Câblage RC522 → ESP32 :
#   NSS→D5  SCK→D18  MOSI→D23  MISO→D19  RST→D22  3.3V→3.3V  GND→GND
# -----------------------------------------------------------------------

from machine import Pin, SPI
import time
import json

# --- Matériel ---
led = Pin(2, Pin.OUT)
led.off()

spi  = SPI(1, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))

from mfrc522 import MFRC522
rfid = MFRC522(spi, gpioRst=22, gpioCs=5)

# --- Noms des niveaux ---
NIVEAUX = {
    1: "Visiteur",
    2: "Membre",
    3: "Admin"
}

# --- Fichier de sauvegarde ---
FICHIER_BADGES = "badges.json"


def charger_badges():
    """Charge la base de badges depuis le fichier JSON."""
    try:
        with open(FICHIER_BADGES, "r") as f:
            return json.load(f)
    except:
        return {}


def sauvegarder_badges(badges):
    """Sauvegarde la base de badges dans le fichier JSON."""
    with open(FICHIER_BADGES, "w") as f:
        json.dump(badges, f)


def uid_vers_str(uid):
    """Convertit un UID en texte lisible : 'AA:BB:CC:DD'."""
    return ':'.join(f'{b:02X}' for b in uid)


def lire_badge():
    """Attend qu'un badge soit présenté et retourne son UID (texte).
    Retourne None si Ctrl+C est pressé."""
    while True:
        stat, _ = rfid.request(rfid.REQIDL)
        if stat == rfid.OK:
            stat, uid = rfid.anticoll()
            if stat == rfid.OK:
                return uid_vers_str(uid)
        time.sleep_ms(200)


def flash_led(duree_ms=1500):
    """Allume la LED bleue pendant la durée indiquée."""
    led.on()
    time.sleep_ms(duree_ms)
    led.off()


# =======================================================================
# MODE PROGRAMMATION
# =======================================================================
def programmation():
    """Enregistrer des badges avec nom, prénom et niveau d'accès."""
    badges = charger_badges()

    print()
    print("=" * 45)
    print("  MODE PROGRAMMATION")
    print("=" * 45)
    print(f"  {len(badges)} badge(s) déjà enregistré(s)")
    print()
    print("  Niveaux : 1=Visiteur  2=Membre  3=Admin")
    print("  Ctrl+C pour revenir au menu")
    print("=" * 45)
    print()

    while True:
        print("Présentez un badge...")
        uid = lire_badge()

        # Vérifier si le badge existe déjà
        if uid in badges:
            info = badges[uid]
            print(f"  Badge déjà enregistré : {info['nom']}")
            print(f"  Niveau actuel : {info['niveau']} ({NIVEAUX[info['niveau']]})")
            rep = input("  Modifier ? (o/n) : ").strip().lower()
            if rep != 'o':
                print()
                time.sleep(1)  # attendre que le badge s'éloigne
                continue

        # Saisir le nom
        nom = input("  Nom et prénom : ").strip()
        if not nom:
            print("  Annulé.")
            print()
            continue

        # Saisir le niveau
        while True:
            try:
                niveau = int(input("  Niveau (1=Visiteur, 2=Membre, 3=Admin) : "))
                if niveau in (1, 2, 3):
                    break
            except ValueError:
                pass
            print("  → Tapez 1, 2 ou 3")

        # Enregistrer
        badges[uid] = {"nom": nom, "niveau": niveau}
        sauvegarder_badges(badges)

        print(f"  ✓ Badge enregistré : {nom} — {NIVEAUX[niveau]}")
        print(f"    UID : {uid}")
        flash_led(500)
        print()

        time.sleep(1)  # attendre que le badge s'éloigne


# =======================================================================
# MODE PRODUCTION
# =======================================================================
def production(niveau_requis=1):
    """Contrôle d'accès : scanner les badges et vérifier le niveau.

    niveau_requis : niveau minimum pour que l'accès soit accordé
                    1 = tout le monde passe
                    2 = Membre et Admin seulement
                    3 = Admin seulement
    """
    badges = charger_badges()

    print()
    print("=" * 45)
    print("  MODE PRODUCTION")
    print("=" * 45)
    print(f"  {len(badges)} badge(s) en base")
    print(f"  Niveau requis : {niveau_requis} ({NIVEAUX.get(niveau_requis, '?')})")
    print("  Ctrl+C pour revenir au menu")
    print("=" * 45)
    print()

    while True:
        stat, _ = rfid.request(rfid.REQIDL)

        if stat == rfid.OK:
            stat, uid = rfid.anticoll()
            if stat == rfid.OK:
                uid_str = uid_vers_str(uid)

                if uid_str in badges:
                    info = badges[uid_str]
                    nom    = info["nom"]
                    niveau = info["niveau"]

                    if niveau >= niveau_requis:
                        # ACCÈS ACCORDÉ
                        print(f"  ✓ ACCÈS ACCORDÉ — {nom}")
                        print(f"    Niveau {niveau} ({NIVEAUX[niveau]})")
                        flash_led(1500)
                    else:
                        # ACCÈS REFUSÉ (niveau insuffisant)
                        print(f"  ✗ ACCÈS REFUSÉ — {nom}")
                        print(f"    Niveau {niveau} ({NIVEAUX[niveau]}) — requis : {niveau_requis} ({NIVEAUX[niveau_requis]})")
                else:
                    # BADGE INCONNU
                    print(f"  ✗ BADGE INCONNU — {uid_str}")

                print()
                time.sleep(1)  # attendre que le badge s'éloigne

        time.sleep_ms(200)


# =======================================================================
# MENU PRINCIPAL
# =======================================================================
def menu():
    """Menu principal — choix du mode."""
    while True:
        print()
        print("=" * 45)
        print("  CONTRÔLE D'ACCÈS RFID — 3 NIVEAUX")
        print("=" * 45)
        print()
        print("  1. Programmation (enregistrer des badges)")
        print("  2. Production — accès Visiteur+ (niveau 1)")
        print("  3. Production — accès Membre+   (niveau 2)")
        print("  4. Production — accès Admin     (niveau 3)")
        print("  5. Lister les badges enregistrés")
        print("  6. Supprimer un badge")
        print()

        choix = input("  Choix (1-6) : ").strip()

        try:
            if choix == '1':
                programmation()
            elif choix == '2':
                production(niveau_requis=1)
            elif choix == '3':
                production(niveau_requis=2)
            elif choix == '4':
                production(niveau_requis=3)
            elif choix == '5':
                lister_badges()
            elif choix == '6':
                supprimer_badge()
        except KeyboardInterrupt:
            print("\n  → Retour au menu")


def lister_badges():
    """Affiche tous les badges enregistrés."""
    badges = charger_badges()
    print()
    if not badges:
        print("  Aucun badge enregistré.")
        return

    print(f"  {len(badges)} badge(s) :")
    print(f"  {'UID':<20} {'Nom':<25} {'Niveau'}")
    print(f"  {'-'*20} {'-'*25} {'-'*15}")
    for uid, info in badges.items():
        n = info['niveau']
        print(f"  {uid:<20} {info['nom']:<25} {n} ({NIVEAUX[n]})")
    print()


def supprimer_badge():
    """Supprimer un badge par scan."""
    badges = charger_badges()
    if not badges:
        print("  Aucun badge enregistré.")
        return

    print()
    print("  Présentez le badge à supprimer...")
    uid = lire_badge()

    if uid in badges:
        info = badges[uid]
        print(f"  Badge trouvé : {info['nom']} — {NIVEAUX[info['niveau']]}")
        rep = input("  Confirmer la suppression ? (o/n) : ").strip().lower()
        if rep == 'o':
            del badges[uid]
            sauvegarder_badges(badges)
            print("  ✓ Badge supprimé.")
        else:
            print("  Annulé.")
    else:
        print(f"  Badge {uid} non trouvé dans la base.")
    print()


# --- Lancement ---
print("Lecteur RFID RC522 initialisé.")
menu()
