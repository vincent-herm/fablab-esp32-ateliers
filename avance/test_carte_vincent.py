# =============================================================================
# test_carte_enim.py — Test complet de la carte Vincent
# =============================================================================
# Vérifie un par un tous les organes de la carte. Autonome : n'importe PAS
# essential.py, pour rester utilisable même si ce fichier manque sur l'ESP32.
#
# BROCHAGE CARTE VINCENT
#   LEDs      bleue 2 · verte 18 · jaune 19 · rouge 23
#   Boutons   bpA 25 · bpB 34 · bpC 39 · bpD 36      (ACTIFS A L'ETAT HAUT)
#   Touch     tp1 15 · tp2 4
#   ADC       p1 35 · p2 33 · ldr 32                  (9 bits -> 0 a 511)
#   NeoPixel  26, 8 LEDs
#   Buzzer    PWM 5
#   DS18B20   27 (OneWire)
#   OLED      SH1106 I2C, SCL 22 / SDA 21, reset 16, adresse 0x3c
#
# ATTENTION — CONFLITS DE BROCHES
#   Le lecteur RFID RC522 utilise SCK 18, MISO 19, MOSI 23 et RST 22.
#   Ces broches sont AUSSI les LEDs verte/jaune/rouge et le SCL de l'OLED.
#   RFID et LEDs ne peuvent donc pas fonctionner en meme temps.
#
# UTILISATION
#   Lancer avec F5 dans Thonny. Appuyer sur bpA pour passer au test suivant.
# =============================================================================

from machine import Pin, PWM, ADC, TouchPad, I2C
import time

# --- Sorties ---
leds = [
    ("bleue",  2, Pin(2,  Pin.OUT)),
    ("verte", 18, Pin(18, Pin.OUT)),
    ("jaune", 19, Pin(19, Pin.OUT)),
    ("rouge", 23, Pin(23, Pin.OUT)),
]

# --- Entrees tout-ou-rien (actives a l'etat HAUT) ---
boutons = [
    ("bpA", Pin(25, Pin.IN)),
    ("bpB", Pin(34, Pin.IN)),
    ("bpC", Pin(39, Pin.IN)),
    ("bpD", Pin(36, Pin.IN)),
]
bpA = boutons[0][1]

# --- Entrees tactiles ---
touches = [("tp1", TouchPad(Pin(15))), ("tp2", TouchPad(Pin(4)))]


def adc9(broche):
    """ADC configure en 9 bits : renvoie 0 a 511."""
    a = ADC(Pin(broche))
    a.atten(ADC.ATTN_11DB)
    a.width(ADC.WIDTH_9BIT)
    return a


analogiques = [
    ("p1  (potentiometre)", adc9(35)),
    ("p2  (potentiometre)", adc9(33)),
    ("ldr (photoresist.)",  adc9(32)),
]


def eteindre_leds():
    for _, _, l in leds:
        l.off()


def barre(valeur, maxi, largeur=30):
    """Bargraphe texte pour le Shell."""
    n = int(valeur / maxi * largeur)
    n = max(0, min(largeur, n))
    return "[" + "#" * n + "-" * (largeur - n) + "]"


def titre(n, texte):
    print()
    print("=" * 56)
    print(f"  TEST {n} — {texte}")
    print("=" * 56)


def attendre_bpA(message="Appuyer sur bpA pour continuer..."):
    """Attend un appui PUIS le relachement (boutons actifs a l'etat haut)."""
    print(f"\n>>> {message}")
    while bpA.value() == 0:
        time.sleep_ms(20)
    while bpA.value() == 1:
        time.sleep_ms(20)
    time.sleep_ms(150)          # anti-rebond


# =============================================================================
print()
print("#" * 56)
print("#  TEST DE LA CARTE VINCENT")
print("#  bpA fait passer d'un test au suivant")
print("#" * 56)

# --- TEST 1 : les 4 LEDs ---------------------------------------------------
titre(1, "Les 4 LEDs")
print("Chaque LED s'allume 0,6 s, dans l'ordre. Verifier visuellement.")
for nom, broche, led in leds:
    print(f"   LED {nom:6s} — GPIO {broche}")
    led.on()
    time.sleep(0.6)
    led.off()
print("\nLes 4 ensemble, 3 clignotements :")
for _ in range(3):
    for _, _, l in leds: l.on()
    time.sleep(0.25)
    eteindre_leds()
    time.sleep(0.25)
attendre_bpA()

# --- TEST 2 : bandeau NeoPixel ---------------------------------------------
titre(2, "Bandeau NeoPixel — 8 LEDs sur GPIO 26")
try:
    from neopixel import NeoPixel
    np = NeoPixel(Pin(26, Pin.OUT), 8)

    def np_eteindre():
        for i in range(8): np[i] = (0, 0, 0)
        np.write()

    print("Balayage rouge, vert, bleu...")
    for couleur in [(60, 0, 0), (0, 60, 0), (0, 0, 60)]:
        for i in range(8):
            np_eteindre()
            np[i] = couleur
            np.write()
            time.sleep_ms(70)
    np_eteindre()

    print("Degrade sur les 8 LEDs...")
    for i in range(8):
        np[i] = (i * 8, 60 - i * 7, 30)
    np.write()
    time.sleep(1.5)
    np_eteindre()
    print("OK — si rien ne s'allume, verifier l'alimentation du bandeau.")
except Exception as e:
    print("ECHEC NeoPixel :", e)
attendre_bpA()

# --- TEST 3 : buzzer -------------------------------------------------------
titre(3, "Buzzer — PWM sur GPIO 5")
try:
    buzzer = PWM(Pin(5))
    # gamme temperee a partir de 880 Hz, comme dans essential.py
    for demi_ton in range(13):
        f = int(2 ** (demi_ton / 12) * 880)
        print(f"   {f:4d} Hz", end="  ")
        buzzer.freq(f)
        buzzer.duty(30)
        time.sleep_ms(140)
    buzzer.duty(0)
    buzzer.deinit()
    print("\nOK — 13 notes, une octave complete.")
except Exception as e:
    print("ECHEC buzzer :", e)
attendre_bpA()

# --- TEST 4 : boutons ------------------------------------------------------
titre(4, "Les 4 boutons — actifs a l'etat HAUT")
print("Appuyer sur bpB, bpC et bpD. L'etat s'affiche en direct.")
print("Terminer par un appui sur bpA.\n")
vus = set()
while True:
    etats = []
    for nom, bp in boutons:
        actif = bp.value() == 1
        if actif:
            vus.add(nom)
        etats.append(f"{nom}:{'APPUYE ' if actif else 'relache'}")
    print("   " + "  ".join(etats), end="\r")
    if bpA.value() == 1:
        break
    time.sleep_ms(80)
while bpA.value() == 1:
    time.sleep_ms(20)
print()
manquants = [n for n, _ in boutons if n not in vus]
print("\nBoutons detectes :", ", ".join(sorted(vus)) if vus else "aucun")
if manquants:
    print("Non testes ou HS :", ", ".join(manquants))
time.sleep_ms(300)

# --- TEST 5 : entrees tactiles ---------------------------------------------
titre(5, "Entrees tactiles tp1 (GPIO 15) et tp2 (GPIO 4)")
print("Poser le doigt sur chaque pastille. La valeur CHUTE au contact.")
print("Repere sur cette carte : ~270 au repos, ~30 doigt pose.")
print("Le tableau de bord bascule a 120 (allumage) / 180 (extinction).")
print("Appuyer sur bpA pour passer a la suite.\n")
while bpA.value() == 0:
    v = [f"{nom}:{tp.read():4d}" for nom, tp in touches]
    print("   " + "   ".join(v), end="\r")
    time.sleep_ms(120)
while bpA.value() == 1:
    time.sleep_ms(20)
print("\n")
time.sleep_ms(300)

# --- TEST 6 : entrees analogiques ------------------------------------------
titre(6, "Analogique — p1, p2 et LDR (9 bits : 0 a 511)")
print("Tourner les potentiometres, masquer puis eclairer la LDR.")
print("Appuyer sur bpA pour passer a la suite.\n")
while bpA.value() == 0:
    v1, v2, v3 = (a.read() for _, a in analogiques)
    print(f"   p1:{v1:3d}  p2:{v2:3d}  ldr:{v3:3d}  {barre(v3, 511, 20)}", end="\r")
    time.sleep_ms(200)
while bpA.value() == 1:
    time.sleep_ms(20)
print()
time.sleep_ms(300)

# --- TEST 7 : capteur de temperature DS18B20 -------------------------------
titre(7, "DS18B20 — capteur de temperature sur GPIO 27")
try:
    import onewire, ds18x20
    ds = ds18x20.DS18X20(onewire.OneWire(Pin(27)))
    capteurs = ds.scan()
    if not capteurs:
        print("Aucun capteur trouve.")
        print("Verifier le cablage et la resistance de tirage 4,7 kohms.")
    else:
        print(f"{len(capteurs)} capteur(s) detecte(s).")
        for i in range(3):
            ds.convert_temp()
            time.sleep_ms(750)      # duree de conversion en 12 bits
            t = ds.read_temp(capteurs[0])
            print(f"   mesure {i + 1} : {t:.2f} degres C")
except Exception as e:
    print("ECHEC DS18B20 :", e)
attendre_bpA()

# --- TEST 8 : ecran OLED ---------------------------------------------------
titre(8, "Ecran OLED SH1106 — I2C, SCL 22 / SDA 21")
try:
    i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
    trouves = i2c.scan()
    print("Adresses I2C detectees :", [hex(a) for a in trouves])
    if 0x3c not in trouves:
        print("L'ecran (0x3c) ne repond pas — verifier le cablage.")
    else:
        from sh1106 import SH1106_I2C
        display = SH1106_I2C(128, 64, i2c, Pin(16), 0x3c)
        display.sleep(False)
        display.fill(0)
        display.text("CARTE VINCENT", 22, 12, 1)
        display.text("test complet", 16, 30, 1)
        display.text("OK !", 48, 48, 1)
        display.show()
        print("OK — le texte doit apparaitre sur l'ecran.")
except ImportError:
    print("Fichier sh1106.py manquant — le copier sur l'ESP32 via Thonny.")
except Exception as e:
    print("ECHEC OLED :", e)

# --- Fin -------------------------------------------------------------------
eteindre_leds()
print()
print("#" * 56)
print("#  TEST TERMINE")
print("#" * 56)
print("""
Recapitulatif des organes verifies :
   1. LEDs bleue / verte / jaune / rouge
   2. Bandeau NeoPixel 8 LEDs
   3. Buzzer
   4. Boutons bpA a bpD
   5. Entrees tactiles tp1 et tp2
   6. Potentiometres p1, p2 et LDR
   7. Capteur DS18B20
   8. Ecran OLED SH1106

Non teste : le lecteur RFID RC522, dont les broches entrent en conflit
avec les LEDs verte, jaune et rouge. Utiliser test_rfid_enim.py separement.
""")
