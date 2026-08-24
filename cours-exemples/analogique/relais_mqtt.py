# relais_mqtt.py — 2 relais + NeoPixel pilotés via MQTT
# -----------------------------------------------------------------------
# Relais 1  → Pin 27    Relais 2 → Pin 14
# NeoPixel  → Pin 26    (8 LEDs)
#
# Broker MQTT gratuit : broker.hivemq.com (public, sans compte)
#
# Sur smartphone → app "IoT MQTT Panel"
#   Broker   : broker.hivemq.com   Port : 1883
#   Switch R1 : fablab/vincent/r1  → "on" / "off"
#   Switch R2 : fablab/vincent/r2  → "on" / "off"
#   Slider Neo : fablab/vincent/neo → 0 à 8 (nombre de LEDs allumées)
#     → dans l'app : Add Panel → Slider, Min=0, Max=8, Step=1
# -----------------------------------------------------------------------

import network
import machine
import ubinascii
from machine import Pin, ADC, I2C
from neopixel import NeoPixel
from sh1106 import SH1106_I2C
from time import sleep_ms, ticks_ms
from umqtt.simple import MQTTClient

# ── À modifier ──────────────────────────────────────────────────────────
SSID      = "NOM_DE_TON_WIFI"
PASSWORD  = "MOT_DE_PASSE_WIFI"
ACTIF_BAS = True   # True = module relais bleu (LOW=ON)

# Topics MQTT — change "vincent" par quelque chose d'unique
TOPIC_R1  = b"fablab/vincent/r1"
TOPIC_R2  = b"fablab/vincent/r2"
TOPIC_NEO = b"fablab/vincent/neo"
TOPIC_POT  = b"fablab/vincent/potar"
TOPIC_OLED = b"fablab/vincent/oled"
TOPIC_SON  = b"fablab/vincent/son"
# ────────────────────────────────────────────────────────────────────────

BROKER    = "broker.hivemq.com"
PORT      = 1883
CLIENT_ID = b"esp32_" + ubinascii.hexlify(machine.unique_id())

# ── Relais ───────────────────────────────────────────────────────────────
r1 = Pin(27, Pin.OUT)
r2 = Pin(14, Pin.OUT)

def set_relais(pin, on):
    pin.value((0 if on else 1) if ACTIF_BAS else (1 if on else 0))

set_relais(r1, False)
set_relais(r2, False)

# ── NeoPixel ─────────────────────────────────────────────────────────────
N_LEDS = 8
np = NeoPixel(Pin(26), N_LEDS)

COULEUR = (0, 30, 80)   # bleu doux — change à ta guise (R, G, B)

def neo_slider(val):
    """Allume 'val' LEDs (0-8), éteint le reste."""
    val = max(0, min(N_LEDS, val))
    for i in range(N_LEDS):
        np[i] = COULEUR if i < val else (0, 0, 0)
    np.write()

neo_slider(0)   # éteint au démarrage

# ── OLED SH1106 ─────────────────────────────────────────────────────────
i2c  = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
oled = SH1106_I2C(128, 64, i2c)
oled.fill(0)
oled.text("En attente...", 0, 28, 1)
oled.show()

def oled_texte(texte):
    """Affiche le texte sur l'OLED, retour à la ligne automatique."""
    oled.fill(0)
    mots   = texte.split(" ")
    ligne  = ""
    y      = 0
    for mot in mots:
        test = (ligne + " " + mot).strip()
        if len(test) <= 16:
            ligne = test
        else:
            if y < 64:
                oled.text(ligne, 0, y, 1)
                y += 10
            ligne = mot
    if ligne and y < 64:
        oled.text(ligne, 0, y, 1)
    oled.show()

# ── Potentiomètre ────────────────────────────────────────────────────────
pot = ADC(Pin(35))
pot.atten(ADC.ATTN_11DB)
pot.width(ADC.WIDTH_9BIT)   # 0 – 511

# ── Capteur de son ───────────────────────────────────────────────────────
mic = ADC(Pin(34))
mic.atten(ADC.ATTN_11DB)
mic.width(ADC.WIDTH_9BIT)   # 0 – 511, silence ≈ 511

def lire_son():
    """100 lectures rapides → amplitude 0-100"""
    mini = 511
    for _ in range(100):
        v = mic.read()
        if v < mini:
            mini = v
    return (511 - mini) * 100 // 511   # 0 = silence, 100 = fort

# ── Connexion WiFi ───────────────────────────────────────────────────────
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)
print(f"Connexion WiFi à {SSID}...")
for _ in range(20):
    if wifi.isconnected():
        break
    sleep_ms(500)
    print(".", end="")

if not wifi.isconnected():
    print("\nErreur WiFi !")
    raise SystemExit

print(f"\nWiFi OK — IP : {wifi.ifconfig()[0]}")

# ── Callback MQTT (reçoit les messages) ──────────────────────────────────
def on_message(topic, msg):
    cmd = msg.decode().strip().lower()
    print(f"MQTT reçu : {topic.decode()} → {cmd}")

    if topic == TOPIC_R1:
        on = cmd == "on"
        set_relais(r1, on)
        print(f"  Relais 1 → {'ON' if on else 'OFF'}")

    elif topic == TOPIC_R2:
        on = cmd == "on"
        set_relais(r2, on)
        print(f"  Relais 2 → {'ON' if on else 'OFF'}")

    elif topic == TOPIC_OLED:
        texte = msg.decode().strip()
        print(f"  OLED → \"{texte}\"")
        oled_texte(texte)

    elif topic == TOPIC_NEO:
        try:
            val = int(float(cmd))
            neo_slider(val)
            print(f"  NeoPixel → {val}/{N_LEDS} LEDs")
        except ValueError:
            pass

# ── Connexion MQTT ───────────────────────────────────────────────────────
def connect_mqtt():
    client = MQTTClient(CLIENT_ID, BROKER, PORT, keepalive=60)
    client.set_callback(on_message)
    client.connect()
    client.subscribe(TOPIC_R1)
    client.subscribe(TOPIC_R2)
    client.subscribe(TOPIC_NEO)
    client.subscribe(TOPIC_OLED)
    print(f"MQTT connecté → {BROKER}")
    print(f"  Écoute : {TOPIC_R1.decode()}")
    print(f"  Écoute : {TOPIC_R2.decode()}")
    print(f"  Écoute : {TOPIC_NEO.decode()}")
    print(f"  Écoute : {TOPIC_OLED.decode()}")
    return client

client        = connect_mqtt()
last_ping     = ticks_ms()
last_pot_pub  = ticks_ms()
last_son_pub  = ticks_ms()
derniere_val  = -1

print("\nEn attente de commandes...")
print("Smartphone : publier 'on' ou 'off' sur les topics\n")

# ── Boucle principale ────────────────────────────────────────────────────
while True:
    try:
        client.check_msg()   # traite les messages entrants (non bloquant)

        # Potentiomètre → Gauge : publie toutes les 200ms si valeur changée
        if ticks_ms() - last_pot_pub > 200:
            pct = pot.read() * 100 // 511   # 0 – 100 %
            if pct != derniere_val:
                client.publish(TOPIC_POT, str(pct))
                derniere_val = pct
            last_pot_pub = ticks_ms()

        # Son → Line graph : publie toutes les 300ms
        if ticks_ms() - last_son_pub > 300:
            niveau = lire_son()
            client.publish(TOPIC_SON, str(niveau))
            last_son_pub = ticks_ms()

        # Keepalive : ping toutes les 30 secondes
        if ticks_ms() - last_ping > 30000:
            client.ping()
            last_ping = ticks_ms()

    except OSError:
        # Reconnexion automatique si connexion perdue
        print("Connexion perdue — reconnexion...")
        sleep_ms(2000)
        try:
            client = connect_mqtt()
            last_ping = ticks_ms()
        except Exception as e:
            print(f"Erreur reconnexion : {e}")

    sleep_ms(100)
