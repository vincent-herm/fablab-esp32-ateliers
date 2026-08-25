# =============================================================================
# enim_serveur_web.py — Tableau de bord web de la carte Vincent
# =============================================================================
# La carte cree son propre reseau WiFi et sert une page web. Depuis un
# smartphone, on pilote toutes les sorties et on lit toutes les entrees.
#
# UTILISATION
#   1. Lancer ce programme dans Thonny (F5)
#   2. Smartphone : reglages WiFi -> se connecter a "CarteVincent"
#                   mot de passe : micropython
#   3. Navigateur -> http://192.168.4.1
#
# PILOTABLE DEPUIS LE TELEPHONE
#   - les 4 LEDs, une par une
#   - le bandeau NeoPixel : couleur libre, jauge, arc-en-ciel
#   - le buzzer : note reglable et gamme complete
#   - l'ecran OLED : on tape un texte, il s'affiche sur la carte
#
# AFFICHE EN DIRECT (rafraichi 2 fois par seconde)
#   - les 4 boutons, les 2 entrees tactiles
#   - les potentiometres p1 et p2, la photoresistance
#   - le DS18B20 et la temperature du processeur
#
# BROCHAGE CARTE VINCENT
#   LEDs      bleue 2 · verte 18 · jaune 19 · rouge 23
#   Boutons   bpA 25 · bpB 34 · bpC 39 · bpD 36     (ACTIFS A L'ETAT HAUT)
#   Touch     tp1 15 · tp2 4
#   ADC       p1 35 · p2 33 · ldr 32                 (9 bits -> 0 a 511)
#   NeoPixel  26, 8 LEDs
#   Buzzer    PWM 5
#   DS18B20   27
#   OLED      SH1106 I2C, SCL 22 / SDA 21, reset 16, adresse 0x3c
#
# ATTENTION : le lecteur RFID RC522 partage ses broches avec les LEDs
# verte, jaune et rouge (18, 19, 23). Il ne peut pas etre utilise ici.
# =============================================================================

import network
import socket
import json
import esp32
import time
from machine import Pin, PWM, ADC, TouchPad, I2C
from neopixel import NeoPixel

# --- Configuration ---------------------------------------------------------
SSID     = "CarteVincent"
PASSWORD = "micropython"

# --- Sorties ---------------------------------------------------------------
LEDS = [
    {"nom": "Bleue", "broche":  2, "pin": Pin(2,  Pin.OUT), "etat": 0},
    {"nom": "Verte", "broche": 18, "pin": Pin(18, Pin.OUT), "etat": 0},
    {"nom": "Jaune", "broche": 19, "pin": Pin(19, Pin.OUT), "etat": 0},
    {"nom": "Rouge", "broche": 23, "pin": Pin(23, Pin.OUT), "etat": 0},
]
for l in LEDS:
    l["pin"].off()

NB_PIXELS = 8
np = NeoPixel(Pin(26, Pin.OUT), NB_PIXELS)

buzzer = PWM(Pin(5))
buzzer.duty(0)

# --- Entrees ---------------------------------------------------------------
BOUTONS = [("bpA", Pin(25, Pin.IN)), ("bpB", Pin(34, Pin.IN)),
           ("bpC", Pin(39, Pin.IN)), ("bpD", Pin(36, Pin.IN))]

TOUCHES = [("tp1", TouchPad(Pin(15))), ("tp2", TouchPad(Pin(4)))]


def adc9(broche):
    """ADC en 9 bits comme dans essential.py : renvoie 0 a 511."""
    a = ADC(Pin(broche))
    a.atten(ADC.ATTN_11DB)
    a.width(ADC.WIDTH_9BIT)
    return a


p1  = adc9(35)
p2  = adc9(33)
ldr = adc9(32)

# --- Ecran OLED (optionnel : le programme tourne sans) ---------------------
oled = None
try:
    from sh1106 import SH1106_I2C
    i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
    if 0x3c in i2c.scan():
        oled = SH1106_I2C(128, 64, i2c, Pin(16), 0x3c)
        oled.sleep(False)
        oled.fill(0)
        oled.text("Carte Vincent", 24, 16, 1)
        oled.text("192.168.4.1", 16, 34, 1)
        oled.show()
except Exception as e:
    print("OLED indisponible :", e)

# --- Capteur DS18B20 -------------------------------------------------------
ds = None
ds_capteurs = []
try:
    import onewire, ds18x20
    ds = ds18x20.DS18X20(onewire.OneWire(Pin(27)))
    ds_capteurs = ds.scan()
    print(f"DS18B20 : {len(ds_capteurs)} capteur(s)")
except Exception as e:
    print("DS18B20 indisponible :", e)


# =============================================================================
# Lecture NON BLOQUANTE du DS18B20
# -----------------------------------------------------------------------
# Le DS18B20 met jusqu'a 750 ms a convertir. Attendre bêtement bloquerait
# le serveur trois quarts de seconde a chaque rafraichissement.
# On procede donc en deux temps : on lance la conversion, et on ne vient
# lire le resultat qu'a la requete suivante, une fois le delai ecoule.
# =============================================================================
_ds_temp    = None
_ds_lance   = 0
_ds_attente = False


def temperature_ds():
    """Renvoie la derniere temperature connue, sans jamais bloquer."""
    global _ds_temp, _ds_lance, _ds_attente
    if not ds_capteurs:
        return None
    maintenant = time.ticks_ms()
    if not _ds_attente:
        ds.convert_temp()                       # on lance la mesure
        _ds_lance   = maintenant
        _ds_attente = True
    elif time.ticks_diff(maintenant, _ds_lance) > 800:
        try:
            _ds_temp = ds.read_temp(ds_capteurs[0])   # on releve le resultat
        except Exception:
            pass
        _ds_attente = False
    return _ds_temp


def temperature_cpu():
    return (esp32.raw_temperature() - 32) / 1.8


# =============================================================================
# NeoPixel — modes d'affichage
# =============================================================================
neo_mode     = "off"
neo_couleur  = (0, 80, 255)
neo_pos      = 0
_neo_dernier = 0


def roue(pos):
    """Convertit 0-255 en couleur arc-en-ciel."""
    pos %= 256
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)


def neo_rafraichir(valeur_jauge=0):
    """Applique le mode courant au bandeau. Appele a chaque requete /data."""
    global neo_pos
    if neo_mode == "off":
        for i in range(NB_PIXELS):
            np[i] = (0, 0, 0)
    elif neo_mode == "uni":
        for i in range(NB_PIXELS):
            np[i] = neo_couleur
    elif neo_mode == "jauge":
        # le potentiometre p1 remplit la barre
        allumees = int(valeur_jauge / 511 * NB_PIXELS + 0.5)
        for i in range(NB_PIXELS):
            np[i] = neo_couleur if i < allumees else (0, 0, 0)
    elif neo_mode == "arc":
        # L'avancement suit le TEMPS ECOULE, pas le nombre d'appels : la
        # vitesse du defilement reste la meme quel que soit le rythme
        # d'interrogation de la page (~16 pas par seconde).
        global _neo_dernier
        maintenant = time.ticks_ms()
        ecoule = time.ticks_diff(maintenant, _neo_dernier)
        if ecoule > 55:
            neo_pos = (neo_pos + max(1, ecoule // 60)) % 256
            _neo_dernier = maintenant
        for i in range(NB_PIXELS):
            np[i] = roue((i * 32 + neo_pos) % 256)
    np.write()


def jouer_note(freq, duree_ms=180):
    """Emet une note sur le buzzer."""
    if freq <= 0:
        buzzer.duty(0)
        return
    buzzer.freq(freq)
    buzzer.duty(40)
    time.sleep_ms(duree_ms)
    buzzer.duty(0)


def jouer_gamme():
    """Les 13 notes d'une octave, a partir de 880 Hz."""
    for demi_ton in range(13):
        jouer_note(int(2 ** (demi_ton / 12) * 880), 110)
        time.sleep_ms(25)


def afficher_oled(texte):
    """Affiche un texte envoye depuis le telephone, sur 3 lignes de 16."""
    if oled is None:
        return False
    oled.fill(0)
    oled.text("Message recu", 8, 2, 1)
    oled.hline(0, 13, 128, 1)
    for i in range(3):
        morceau = texte[i * 16:(i + 1) * 16]
        if morceau:
            oled.text(morceau, 2, 22 + i * 12, 1)
    oled.show()
    return True


def url_decode(s):
    """Decode les %20, %C3%A9... d'une URL. MicroPython n'a pas urllib."""
    s = s.replace("+", " ")
    morceaux = s.split("%")
    if len(morceaux) == 1:
        return s
    octets = bytearray(morceaux[0], "utf-8")
    for m in morceaux[1:]:
        try:
            octets.append(int(m[:2], 16))
            octets.extend(bytearray(m[2:], "utf-8"))
        except Exception:
            octets.extend(bytearray(m, "utf-8"))
    try:
        return bytes(octets).decode("utf-8")
    except Exception:
        return s


def lire_param(ligne, cle, defaut=None):
    """Extrait une valeur d'une URL : 'GET /led?n=2&v=1 HTTP/1.1' -> '2'."""
    try:
        apres = ligne.split(cle + "=")[1]
        return apres.split("&")[0].split(" ")[0]
    except Exception:
        return defaut


# =============================================================================
# Point d'acces WiFi
# =============================================================================
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD, authmode=network.AUTH_WPA_WPA2_PSK)
while not ap.active():
    time.sleep_ms(100)

print()
print("=" * 52)
print(f"  Reseau WiFi : {SSID}")
print(f"  Mot de passe : {PASSWORD}")
print(f"  Adresse      : http://{ap.ifconfig()[0]}")
print("=" * 52)
print()

# =============================================================================
# La page web
# =============================================================================
def page_html():
    """Genere le tableau de bord. Les valeurs sont ensuite mises a jour
    en direct par le JavaScript, qui interroge /data toutes les 150 ms."""

    cellules = "".join(
        f'<div class="etat"><div class="etat-nom">{nom}</div>'
        f'<div class="voyant" id="e-{nom}"></div></div>'
        for nom, _ in BOUTONS
    ) + "".join(
        f'<div class="etat"><div class="etat-nom">{nom}</div>'
        f'<div class="voyant" id="e-{nom}"></div>'
        f'<div class="etat-val" id="v-{nom}">-</div></div>'
        for nom, _ in TOUCHES
    )

    boutons_led = "".join(
        f'<button class="led-btn" id="led{i}" onclick="basculeLed({i})">'
        f'<span class="pastille" id="pastille{i}"></span>{l["nom"]}'
        f'<em>GPIO {l["broche"]}</em></button>'
        for i, l in enumerate(LEDS)
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>Carte Vincent</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      background: #0f0f1a; color: #e2e8f0;
      padding: 20px 16px 40px; max-width: 440px; margin: 0 auto;
    }}
    header {{
      text-align: center; padding: 18px 0 22px;
      border-bottom: 1px solid #1e293b; margin-bottom: 18px;
    }}
    header h1 {{
      font-size: 0.9rem; color: #38bdf8; letter-spacing: 3px;
      font-weight: 700; text-transform: uppercase;
    }}
    header p {{ color: #475569; font-size: 0.75rem; margin-top: 4px; }}

    .card {{
      background: #1e293b; border: 1px solid #334155;
      border-radius: 18px; padding: 20px 18px; margin-bottom: 14px;
    }}
    .card-label {{
      font-size: 0.65rem; color: #64748b; text-transform: uppercase;
      letter-spacing: 1.5px; margin-bottom: 16px;
    }}

    /* --- LEDs --- */
    .leds {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .led-btn {{
      display: flex; align-items: center; gap: 10px;
      background: #0f172a; border: 1px solid #334155; color: #cbd5e1;
      border-radius: 12px; padding: 12px 14px; font-size: 0.85rem;
      font-weight: 600; cursor: pointer; text-align: left;
    }}
    .led-btn em {{
      font-style: normal; font-size: 0.6rem; color: #475569;
      margin-left: auto;
    }}
    .pastille {{
      width: 16px; height: 16px; border-radius: 50%;
      background: #334155; flex-shrink: 0;
      transition: background .25s, box-shadow .25s;
    }}
    .on0 {{ background: #3b82f6 !important; box-shadow: 0 0 14px #3b82f6aa; }}
    .on1 {{ background: #22c55e !important; box-shadow: 0 0 14px #22c55eaa; }}
    .on2 {{ background: #eab308 !important; box-shadow: 0 0 14px #eab308aa; }}
    .on3 {{ background: #ef4444 !important; box-shadow: 0 0 14px #ef4444aa; }}

    /* --- Boutons generiques --- */
    .row {{ display: flex; gap: 9px; flex-wrap: wrap; }}
    .btn {{
      flex: 1; min-width: 72px; background: #0f172a;
      border: 1px solid #334155; color: #cbd5e1; border-radius: 11px;
      padding: 11px 8px; font-size: 0.78rem; font-weight: 600; cursor: pointer;
    }}
    .btn.actif {{ background: #38bdf8; border-color: #38bdf8; color: #0f172a; }}

    input[type=color] {{
      width: 100%; height: 42px; border: 1px solid #334155;
      border-radius: 11px; background: #0f172a; cursor: pointer; margin-top: 10px;
    }}
    input[type=range] {{ width: 100%; margin-top: 12px; accent-color: #38bdf8; }}
    input[type=text] {{
      width: 100%; background: #0f172a; border: 1px solid #334155;
      color: #e2e8f0; border-radius: 11px; padding: 12px 14px;
      font-size: 0.9rem; margin-bottom: 10px;
    }}

    /* --- Capteurs --- */
    .mesure {{
      display: flex; align-items: center; gap: 12px; margin-bottom: 14px;
    }}
    .mesure-nom {{ font-size: 0.75rem; color: #94a3b8; width: 84px; flex-shrink: 0; }}
    .jauge {{
      flex: 1; height: 8px; background: #0f172a;
      border-radius: 4px; overflow: hidden;
    }}
    .jauge span {{
      display: block; height: 100%; width: 0%;
      background: linear-gradient(90deg, #38bdf8, #22c55e); transition: width .2s;
    }}
    .mesure-val {{
      font-size: 0.8rem; font-weight: 700; color: #e2e8f0;
      width: 52px; text-align: right; font-variant-numeric: tabular-nums;
    }}

    .etats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; }}
    .etat {{
      background: #0f172a; border: 1px solid #334155; border-radius: 11px;
      padding: 10px 6px; text-align: center;
    }}
    .etat-nom {{ font-size: 0.62rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }}
    .etat-val {{ font-size: 0.7rem; margin-top: 4px; color: #475569;
                 font-variant-numeric: tabular-nums; }}
    .voyant {{
      width: 24px; height: 24px; border-radius: 50%;
      background: #0f172a; border: 1px solid #334155;
      margin: 9px auto 0;
      transition: background .15s, box-shadow .15s, border-color .15s;
    }}
    .voyant.allume {{
      background: #22c55e; border-color: #22c55e;
      box-shadow: 0 0 16px #22c55ecc;
    }}

    .explic {{
      margin-top: 12px; padding: 11px 13px;
      background: #0f172a; border-left: 3px solid #38bdf8;
      border-radius: 0 9px 9px 0;
      font-size: 0.72rem; color: #94a3b8; line-height: 1.5;
    }}
    .explic b {{ color: #cbd5e1; }}

    footer {{ text-align: center; color: #334155; font-size: 0.68rem; margin-top: 24px; }}
  </style>
</head>
<body>

  <header>
    <h1>Carte Vincent</h1>
    <p>MicroPython &middot; ESP32 &middot; Fablab Payzac</p>
  </header>

  <!-- ===================== SORTIES ===================== -->
  <div class="card">
    <div class="card-label">Les 4 LEDs</div>
    <div class="leds">{boutons_led}</div>
  </div>

  <div class="card">
    <div class="card-label">Bandeau NeoPixel</div>
    <div class="row">
      <button class="btn" id="neo-off"   onclick="neo('off')">Eteint</button>
      <button class="btn" id="neo-uni"   onclick="neo('uni')">Couleur</button>
      <button class="btn" id="neo-jauge" onclick="neo('jauge')">Jauge p1</button>
      <button class="btn" id="neo-arc"   onclick="neo('arc')">Arc-en-ciel</button>
    </div>
    <input type="color" id="couleur" value="#0050ff" onchange="neo(modeNeo)">
    <div class="explic" id="explic-neo"></div>
  </div>

  <div class="card">
    <div class="card-label">Buzzer</div>
    <div class="row">
      <button class="btn" onclick="note()">Jouer la note</button>
      <button class="btn" onclick="fetch('/gamme')">Gamme complete</button>
    </div>
    <input type="range" id="freq" min="220" max="2000" value="880" oninput="majFreq()">
    <div style="text-align:center;color:#64748b;font-size:0.75rem;margin-top:6px">
      <span id="freq-val">880</span> Hz
    </div>
  </div>

  <div class="card">
    <div class="card-label">Ecran OLED</div>
    <input type="text" id="msg" maxlength="48" placeholder="Ton message pour l'ecran...">
    <div class="row"><button class="btn" onclick="envoyerTexte()">Afficher sur la carte</button></div>
  </div>

  <!-- ===================== ENTREES ===================== -->
  <div class="card">
    <div class="card-label">Boutons et touches</div>
    <div class="etats" id="etats">{cellules}</div>
    <p style="font-size:0.65rem;color:#475569;margin-top:12px;text-align:center">
      Boutons actifs a l'etat HAUT &middot; touche : ~270 au repos, ~30 au contact
    </p>
  </div>

  <div class="card">
    <div class="card-label">Mesures analogiques</div>
    <div class="mesure">
      <span class="mesure-nom">p1</span>
      <span class="jauge"><span id="j-p1"></span></span>
      <span class="mesure-val" id="v-p1">-</span>
    </div>
    <div class="mesure">
      <span class="mesure-nom">p2</span>
      <span class="jauge"><span id="j-p2"></span></span>
      <span class="mesure-val" id="v-p2">-</span>
    </div>
    <div class="mesure">
      <span class="mesure-nom">Lumiere</span>
      <span class="jauge"><span id="j-ldr"></span></span>
      <span class="mesure-val" id="v-ldr">-</span>
    </div>
  </div>

  <div class="card">
    <div class="card-label">Temperatures</div>
    <div class="mesure">
      <span class="mesure-nom">DS18B20</span>
      <span class="jauge"><span id="j-ds"></span></span>
      <span class="mesure-val" id="v-ds">-</span>
    </div>
    <div class="mesure">
      <span class="mesure-nom">Processeur</span>
      <span class="jauge"><span id="j-cpu"></span></span>
      <span class="mesure-val" id="v-cpu">-</span>
    </div>
  </div>

  <footer>
    <span id="voyant" style="display:inline-block;width:7px;height:7px;
      border-radius:50%;background:#475569;margin-right:6px;
      vertical-align:middle"></span><span id="liaison">connexion...</span>
    &nbsp;&middot;&nbsp;cycle <span id="cycle">-</span>
  </footer>

<script>
  var modeNeo = 'off';

  // --- Detection tactile ---------------------------------------------
  // Mesures relevees sur la carte : ~270 au repos, ~30 doigt pose.
  // On bascule au milieu, avec une HYSTERESIS : il faut descendre sous
  // 120 pour allumer, mais remonter au-dessus de 180 pour eteindre.
  // Cette zone morte de 60 evite le clignotement quand la valeur hesite
  // autour du seuil — meme principe que les deux seuils de la LDR dans
  // l'atelier Lumiere automatique.
  var TOUCHE_ON  = 120;   // en dessous -> le doigt est pose
  var TOUCHE_OFF = 180;   // au dessus  -> le doigt est retire
  var etatTouche = {{}};  // memorise l'etat de chaque pastille

  function basculeLed(i) {{
    fetch('/led?n=' + i).catch(function() {{}});
  }}

  // Ce que fait chaque mode. Couleur et Jauge utilisent la MEME couleur :
  // la difference est le nombre de LEDs allumees.
  var EXPLICATIONS = {{
    off:   "Le bandeau est <b>eteint</b>. Le selecteur de couleur ci-dessus " +
           "n'a aucun effet tant qu'un autre mode n'est pas choisi.",
    uni:   "<b>Couleur</b> : les 8 LEDs affichent toutes la meme teinte, " +
           "en permanence. Le bandeau sert d'eclairage ou de temoin d'etat. " +
           "Change la couleur ci-dessus, elle s'applique aussitot.",
    jauge: "<b>Jauge p1</b> : meme couleur, mais le <b>nombre</b> de LEDs " +
           "allumees suit le potentiometre p1. C'est un bargraphe : p1 au " +
           "minimum eteint tout, au maximum allume les 8. Tourne p1 pour voir.",
    arc:   "<b>Arc-en-ciel</b> : chaque LED prend une teinte differente et " +
           "l'ensemble defile. Le selecteur de couleur est ignore, les " +
           "teintes sont calculees par la fonction roue()."
  }};

  function neo(mode) {{
    modeNeo = mode;
    document.getElementById('explic-neo').innerHTML = EXPLICATIONS[mode];
    var c = document.getElementById('couleur').value;   // "#rrggbb"
    fetch('/neo?mode=' + mode + '&c=' + c.substring(1)).catch(function() {{}});
    ['off','uni','jauge','arc'].forEach(function(m) {{
      document.getElementById('neo-' + m).classList.toggle('actif', m === mode);
    }});
  }}

  function majFreq() {{
    document.getElementById('freq-val').textContent =
      document.getElementById('freq').value;
  }}

  function note() {{
    fetch('/buz?f=' + document.getElementById('freq').value).catch(function() {{}});
  }}

  function envoyerTexte() {{
    var t = document.getElementById('msg').value;
    fetch('/oled?t=' + encodeURIComponent(t)).catch(function() {{}});
  }}

  // --- Rafraichissement des entrees ---
  var echecs = 0;

  function liaison(ok, message) {{
    document.getElementById('voyant').style.background = ok ? '#22c55e' : '#ef4444';
    document.getElementById('liaison').textContent = message;
  }}

  function rafraichir(termine) {{
    if (!termine) termine = function() {{}};
    fetch('/data')
      .then(function(r) {{
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      }})
      .then(function(d) {{
        echecs = 0;
        liaison(true, 'carte connectee');

        // LEDs : etat reel renvoye par la carte
        d.leds.forEach(function(etat, i) {{
          document.getElementById('pastille' + i)
                  .classList.toggle('on' + i, etat === 1);
        }});

        // Boutons : le voyant s'allume quand la broche est a l'etat haut
        d.boutons.forEach(function(b) {{
          document.getElementById('e-' + b[0])
                  .classList.toggle('allume', b[1] === 1);
        }});

        // Touches : le voyant s'allume quand la valeur passe sous le seuil.
        // La valeur reste affichee sous le voyant, pour pouvoir regler SEUIL.
        d.touches.forEach(function(t) {{
          var nom = t[0], v = t[1];
          if (v < TOUCHE_ON)       etatTouche[nom] = true;
          else if (v > TOUCHE_OFF) etatTouche[nom] = false;
          // entre les deux : on garde l'etat precedent
          document.getElementById('e-' + nom)
                  .classList.toggle('allume', etatTouche[nom] === true);
          document.getElementById('v-' + nom).textContent = v;
        }});

        // Analogique (9 bits : 0 a 511)
        maj('p1',  d.p1,  511, d.p1);
        maj('p2',  d.p2,  511, d.p2);
        maj('ldr', d.ldr, 511, d.ldr);

        // Temperatures, ramenees sur une echelle 0-50 degres
        if (d.ds === null) {{
          document.getElementById('v-ds').textContent = 'absent';
        }} else {{
          maj('ds', d.ds, 50, d.ds.toFixed(1) + '\\u00B0');
        }}
        maj('cpu', d.cpu, 80, d.cpu.toFixed(1) + '\\u00B0');
        termine();
      }})
      .catch(function(e) {{
        echecs++;
        liaison(false, 'pas de reponse (' + echecs + ') : ' + e.message);
        termine();
      }});
  }}

  function maj(id, valeur, maxi, texte) {{
    var pct = Math.max(0, Math.min(100, valeur / maxi * 100));
    document.getElementById('j-' + id).style.width = pct + '%';
    document.getElementById('v-' + id).textContent = texte;
  }}

  // --- Cadence -------------------------------------------------------
  // On ENCHAINE les interrogations au lieu d'utiliser setInterval :
  // la suivante ne part qu'une fois la precedente terminee. Avec
  // setInterval, une carte momentanement lente voit les requetes
  // s'empiler, et le retard grandit sans jamais se resorber.
  var PERIODE = 150;        // millisecondes entre deux mesures

  function boucle() {{
    var depart = Date.now();
    rafraichir(function() {{
      var cycle = Date.now() - depart;
      document.getElementById('cycle').textContent = cycle + ' ms';
      setTimeout(boucle, Math.max(0, PERIODE - cycle));
    }});
  }}

  neo('off');
  boucle();
</script>

</body>
</html>"""


# =============================================================================
# Le serveur
# =============================================================================
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # libere le port
s.bind(("", 80))
s.listen(5)
print("Serveur demarre — connecte-toi puis ouvre http://192.168.4.1")
print("Ctrl+C pour arreter\n")

REPONSE_VIDE = "HTTP/1.1 204 No Content\r\nConnection: close\r\n\r\n"

try:
    while True:
        conn, addr = s.accept()
        try:
            conn.settimeout(3.0)                  # jamais bloque sur un client parti
            requete = conn.recv(1024).decode()
            ligne   = requete.split("\r\n")[0]    # premiere ligne seulement

            # ---------- Etat de toutes les entrees, en JSON ----------
            if "GET /data" in ligne:
                v_p1 = p1.read()
                neo_rafraichir(v_p1)              # la jauge suit p1
                etat = {
                    "leds":    [l["etat"] for l in LEDS],
                    "boutons": [[nom, 1 if bp.value() == 1 else 0] for nom, bp in BOUTONS],
                    "touches": [[nom, tp.read()] for nom, tp in TOUCHES],
                    "p1":      v_p1,
                    "p2":      p2.read(),
                    "ldr":     ldr.read(),
                    "ds":      temperature_ds(),
                    "cpu":     temperature_cpu(),
                }
                corps = json.dumps(etat)
                conn.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                          "Connection: close\r\n\r\n")
                conn.send(corps)

            # ---------- Bascule d'une LED ----------
            elif "GET /led" in ligne:
                n = lire_param(ligne, "n")
                try:
                    i = int(n)
                    if 0 <= i < len(LEDS):
                        LEDS[i]["etat"] ^= 1                    # 0 -> 1, 1 -> 0
                        LEDS[i]["pin"].value(LEDS[i]["etat"])
                        print(f"LED {LEDS[i]['nom']} -> {'ON' if LEDS[i]['etat'] else 'OFF'}")
                except Exception:
                    pass
                conn.send(REPONSE_VIDE)

            # ---------- Mode du bandeau NeoPixel ----------
            elif "GET /neo" in ligne:
                mode = lire_param(ligne, "mode", "off")
                coul = lire_param(ligne, "c")
                if mode in ("off", "uni", "jauge", "arc"):
                    neo_mode = mode
                if coul and len(coul) >= 6:
                    try:
                        # "ff8800" -> (255, 136, 0), divise par 3 pour ne pas eblouir
                        neo_couleur = (int(coul[0:2], 16) // 3,
                                       int(coul[2:4], 16) // 3,
                                       int(coul[4:6], 16) // 3)
                    except Exception:
                        pass
                neo_rafraichir(p1.read())
                print(f"NeoPixel -> {neo_mode} {neo_couleur}")
                conn.send(REPONSE_VIDE)

            # ---------- Une note sur le buzzer ----------
            elif "GET /buz" in ligne:
                f = lire_param(ligne, "f", "880")
                try:
                    jouer_note(int(f))
                except Exception:
                    pass
                conn.send(REPONSE_VIDE)

            # ---------- La gamme complete ----------
            elif "GET /gamme" in ligne:
                conn.send(REPONSE_VIDE)
                conn.close()
                jouer_gamme()          # apres avoir repondu : ~1,7 s de musique
                continue

            # ---------- Texte a afficher sur l'OLED ----------
            elif "GET /oled" in ligne:
                texte = url_decode(lire_param(ligne, "t", "") or "")
                ok = afficher_oled(texte)
                print("OLED :", texte if ok else "(ecran absent)")
                conn.send(REPONSE_VIDE)

            # ---------- La page ----------
            elif "GET / " in ligne:
                html = page_html()
                conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
                          "Connection: close\r\n\r\n")
                # envoi par morceaux : la page depasse la taille d'un seul send
                for i in range(0, len(html), 512):
                    conn.send(html[i:i + 512])

            else:
                conn.send("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")

        except OSError:
            pass          # connexion coupee par le client — normal sur mobile
        finally:
            try:
                conn.close()
            except Exception:
                pass      # /gamme l'a deja fermee avant de jouer

except KeyboardInterrupt:
    print("\nArret du serveur.")
    buzzer.duty(0)
    for l in LEDS:
        l["pin"].off()
    for i in range(NB_PIXELS):
        np[i] = (0, 0, 0)
    np.write()
    s.close()

# =============================================================================
# EXPERIENCES A TESTER
#   - Change le nom du reseau : SSID = "ESP32-TonPrenom"
#   - Change PERIODE (en bas de la page) : 60 ms pour du temps reel,
#     500 ms pour menager la carte. Le cycle reel s'affiche en pied de page.
#   - Fais piloter la couleur du bandeau par la photoresistance
#   - Ajoute une alarme : le buzzer sonne si le DS18B20 depasse 30 degres
#   - Escape game : n'affiche le message sur l'OLED que si bpA est appuye
#
# A RETENIR — pourquoi /data en JSON plutot qu'une route par capteur
#   La manip 09 avait une route /temp pour une seule valeur. Ici il y en a
#   douze : douze requetes deux fois par seconde saturerait la carte.
#   Une seule requete qui renvoie tout est infiniment plus economique.
#   C'est exactement ce que fait une API web.
#
# A RETENIR — la lecture non bloquante du DS18B20
#   Le capteur met 750 ms a convertir. Attendre bloquerait le serveur trois
#   quarts de seconde a chaque mesure. On lance donc la conversion, et on
#   releve le resultat a la requete suivante : le serveur reste fluide.
# =============================================================================
