# =============================================================================
# grafcet_rfid.py — Sas d'accès RFID / 3 branches parallèles
# =============================================================================
# GRAFCET 8 étapes sur carte ENIM + lecteur RFID RC522.
#
# GRAFCET :
#
#   Étape 0 — Veille
#     [C] NeoPixel chenillard bleu
#     [C] OLED "Présentez votre badge"
#       │ T0 : badge détecté → DIVERGENCE ET (3 branches simultanées)
#       ├──────────────────────┬────────────────────────────┐
#   Branch G (NeoPixel)   Branch M (LEDs)           Branch D (OLED)
#   Étape 1 — Scan NP      Étape 3 — Scan LED         Étape 5 — Scan OLED
#     [C] pulse orange       [C] led_bleue clignote     [C] "Identification..."
#       │ T1 : auto             │ T2 : auto                 │ T3 : auto
#   Étape 2 — Résultat NP  Étape 4 — Résultat LED     Étape 6 — Résultat OLED
#     [C] couleur/arc-ciel   [C] vert=OK rouge=refus     [C] nom + niveau
#       └─────────────── T4 : CONVERGENCE ET ───────────────┘
#                               │ (É2 ET É4 ET É6 actives)
#                           Étape 7 — Maintien 3 s
#                             [C] arc-en-ciel si Admin
#                               │ T5 : tempo >= 3000
#                           retour Étape 0
#
# SORTIES :
#   NeoPixel  (Pin 26) — chenillard veille / pulse scan / couleur résultat
#   led_bleue (Pin  2) — clignote 4 Hz pendant scan
#   led_verte (Pin 18) — accès accordé (niveau >= 1)
#   led_jaune (Pin 19) — admin uniquement
#   led_rouge (Pin 23) — accès refusé (badge inconnu)
#   buzzer    (Pin  5) — bip OK / 3 bips refus
#   OLED SH1106 (I2C scl=22 sda=21, pas de GPIO RST) — messages
#
# ENTRÉES :
#   RFID RC522 (SPI : SCK=14 MOSI=13 MISO=16 NSS=32 RST→3.3V)
#   bpA (Pin 25) — reset d'urgence
#
# Résultat selon niveau du badge :
#   0 Inconnu  → NeoPixel rouge  / led_rouge / OLED "Accès refusé"
#   1 Visiteur → NeoPixel bleu   / led_verte / OLED "Bienvenue Visiteur"
#   2 Membre   → NeoPixel vert   / led_verte / OLED "Bienvenue Membre"
#   3 Admin    → arc-en-ciel     / led_verte + led_jaune / OLED "ADMIN"
#
# Fichiers requis : grafcet_complet.py, essential.py,
#                   mfrc522.py, sh1106.py, badges.json
# =============================================================================

from machine import SPI, Pin, I2C
from time import ticks_ms, sleep_ms
from grafcet_complet import Grafcet
from essential import synchro_ms, bpA, led_bleue, led_verte, led_jaune, led_rouge, buzzer, np
from mfrc522 import MFRC522
from sh1106 import SH1106_I2C
import json


# =============================================================================
# MATÉRIEL
# =============================================================================

# RFID RC522 — SPI1 (HSPI) : RST câblé sur 3.3V, pas de GPIO RST
spi  = SPI(1, baudrate=1000000, sck=Pin(14), mosi=Pin(13), miso=Pin(16))
rfid = MFRC522(spi, gpioRst=None, gpioCs=32)

# OLED SH1106 128×64 — pas de GPIO RST (None)
i2c     = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
display = SH1106_I2C(128, 64, i2c, None, 0x3c)
display.sleep(False)


# =============================================================================
# BADGES
# =============================================================================

NIVEAUX        = {0: "Inconnu", 1: "Visiteur", 2: "Membre", 3: "Admin"}
FICHIER_BADGES = "badges.json"


def charger_badges():
    try:
        with open(FICHIER_BADGES) as f:
            return json.load(f)
    except:
        return {}


def uid_vers_str(uid):
    return ':'.join(f'{b:02X}' for b in uid)


badges = charger_badges()

# État courant du badge scanné
badge_detecte = False
badge_uid     = ""
badge_niveau  = 0
badge_nom     = ""


# =============================================================================
# UTILITAIRES
# =============================================================================

def arc_en_ciel(h):
    """Teinte (0-255) → triplet RGB, luminosité réduite."""
    h = h % 256
    B = 35
    if h < 85:
        return (B - h * B // 85, h * B // 85, 0)
    elif h < 170:
        h -= 85
        return (0, B - h * B // 85, h * B // 85)
    else:
        h -= 170
        return (h * B // 85, 0, B - h * B // 85)


def np_set_all(color):
    for i in range(8):
        np[i] = color
    np.write()


def np_eteindre():
    np_set_all((0, 0, 0))


def leds_off():
    led_bleue.value(0)
    led_verte.value(0)
    led_jaune.value(0)
    led_rouge.value(0)


def couleur_niveau(niveau):
    """Couleur NeoPixel fixe selon le niveau (None = arc-en-ciel pour admin)."""
    if niveau == 0: return (35, 0,  0)   # rouge
    if niveau == 1: return (0,  0, 35)   # bleu
    if niveau == 2: return (0, 35,  0)   # vert
    return None                           # admin : arc-en-ciel


def bip_ok():
    """Bip court 880 Hz — accès accordé (bloquant ~80 ms)."""
    buzzer.init(freq=880, duty=100)
    sleep_ms(80)
    buzzer.deinit()


def bip_refus():
    """3 bips graves — accès refusé (bloquant ~330 ms)."""
    for _ in range(3):
        buzzer.init(freq=330, duty=80)
        sleep_ms(60)
        buzzer.deinit()
        sleep_ms(50)


def oled_veille():
    display.fill(0)
    display.text("Fablab Ardèche", 4, 10)
    display.text("Presentez votre", 0, 26)
    display.text("badge RFID", 20, 40)
    display.show()


def oled_resultat():
    display.fill(0)
    if badge_niveau == 0:
        display.text("ACCES REFUSE", 8, 10)
        display.text("Badge inconnu", 4, 28)
        uid_court = badge_uid[:16]
        display.text(uid_court, 0, 46)
    else:
        display.text("Bienvenue !", 16, 4)
        nom = badge_nom[:14]
        display.text(nom, max(0, (128 - len(nom) * 8) // 2), 22)
        display.text(NIVEAUX[badge_niveau], 0, 40)
        if badge_niveau == 3:
            display.text("** ADMIN **", 16, 54)
    display.show()


# =============================================================================
# GRAFCET — 8 étapes, 3 branches parallèles
# =============================================================================

# nb_fronts=0 : la détection RFID est gérée manuellement dans lire_entrees()
g = Grafcet(nb_etapes=8, nb_fronts=0)

T = [
    (0, (0,),       (1, 3, 5)),  # T0 : badge → DIVERGENCE ET (3 branches)
    (1, (1,),       (2,)),        # T1 : auto → résultat NeoPixel
    (2, (3,),       (4,)),        # T2 : auto → résultat LEDs
    (3, (5,),       (6,)),        # T3 : auto → résultat OLED
    (4, (2, 4, 6),  (7,)),        # T4 : CONVERGENCE ET (É2 ET É4 ET É6)
    (5, (7,),       (0,)),        # T5 : 3 s → retour veille
]

transitions = [False] * 6

# Init sorties
np_eteindre()
leds_off()


# =============================================================================
# CYCLE GRAFCET
# =============================================================================

def gerer_actions():

    # --- É0 [C] : chenillard bleu lent ---
    if g.rising[0]:
        leds_off()
        oled_veille()

    if g.etapes[0]:
        pos = (g.tempo[0] // 180) % 8
        for i in range(8):
            np[i] = (0, 0, 25) if i == pos else (0, 0, 0)
        np.write()

    # --- É1 [C] : NeoPixel pulse orange (scan en cours) ---
    if g.etapes[1]:
        t = g.tempo[1] % 600
        v = t if t < 300 else 600 - t
        v = v * 35 // 300
        np_set_all((v, v // 3, 0))

    # --- É2 [C] : NeoPixel couleur résultat ---
    if g.rising[2]:
        c = couleur_niveau(badge_niveau)
        if c:
            np_set_all(c)

    if g.etapes[2] and badge_niveau == 3:   # admin : arc-en-ciel animé
        hue = (ticks_ms() // 10) % 256
        for i in range(8):
            np[i] = arc_en_ciel((hue + i * 32) % 256)
        np.write()

    # --- É3 [C] : led_bleue clignote 4 Hz ---
    if g.etapes[3]:
        led_bleue.value(ticks_ms() % 250 < 125)

    # --- É4 [C] : LEDs résultat + buzzer (sur rising) ---
    if g.rising[4]:
        led_bleue.value(0)
        if badge_niveau > 0:
            led_verte.value(1)
            if badge_niveau == 3:
                led_jaune.value(1)
            bip_ok()
        else:
            led_rouge.value(1)
            bip_refus()

    # --- É5 [C] : OLED "Identification en cours..." ---
    if g.rising[5]:
        display.fill(0)
        display.text("Identification", 6, 22)
        display.text("en cours...", 18, 38)
        display.show()

    # --- É6 [C] : OLED résultat ---
    if g.rising[6]:
        oled_resultat()

    # --- É7 [C] : maintien 3 s — arc-en-ciel admin continu ---
    if g.etapes[7] and badge_niveau == 3:
        hue = (ticks_ms() // 10) % 256
        for i in range(8):
            np[i] = arc_en_ciel((hue + i * 32) % 256)
        np.write()


def affecter_sorties():
    pass


def lire_entrees():
    global badge_detecte, badge_uid, badge_niveau, badge_nom

    # Lecture RFID non-bloquante — seulement en veille (É0)
    if g.etapes[0] and not badge_detecte:
        stat, _ = rfid.request(rfid.REQIDL)
        if stat == rfid.OK:
            stat, raw_uid = rfid.anticoll()
            if stat == rfid.OK:
                uid_str      = uid_vers_str(raw_uid)
                badge_uid    = uid_str
                if uid_str in badges:
                    info         = badges[uid_str]
                    badge_nom    = info["nom"]
                    badge_niveau = info["niveau"]
                else:
                    badge_nom    = uid_str
                    badge_niveau = 0
                badge_detecte = True
                print(f"Badge : {badge_nom} — {NIVEAUX[badge_niveau]}")


def calculer_transitions():
    transitions[0] = badge_detecte
    transitions[1] = True          # branch G : passage immédiat vers résultat
    transitions[2] = True          # branch M : passage immédiat vers résultat
    transitions[3] = True          # branch D : passage immédiat vers résultat
    transitions[4] = True          # CONVERGENCE ET (moteur vérifie É2+É4+É6)
    transitions[5] = g.tempo[7] >= 3000


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

print("=== Grafcet RFID — Sas d'accès 3 niveaux ===")
print(f"{len(badges)} badge(s) en mémoire")
print("Présentez un badge RFID — bpA = reset d'urgence")

oled_veille()

while True:
    g.franchir(T, transitions)

    # Reset d'urgence — bpA remet tout à zéro
    if bpA.value():
        g.reinitialiser()
        np_eteindre()
        leds_off()
        badge_detecte = False
        display.fill(0)
        display.text("RESET", 44, 28)
        display.show()
        print("Reset")

    g.tick(20)
    gerer_actions()
    affecter_sorties()
    lire_entrees()
    g.detecter_fronts_entrees()
    calculer_transitions()
    synchro_ms(20)
