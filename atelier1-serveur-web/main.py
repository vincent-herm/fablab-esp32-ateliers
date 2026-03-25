# Atelier 01 — Serveur web avec ESP32
# Fablab Ardèche — MicroPython
#
# L'ESP32 crée son propre réseau WiFi et sert un tableau de bord HTML :
#   - Contrôle ON/OFF de la LED
#   - Slider de luminosité (PWM) — glisser le doigt = LED qui varie
#   - Température du processeur en temps réel
#
# Matériel : ESP32, LED sur GPIO2, résistance 220Ω
# Connexion : rejoindre le WiFi "ESP32-Fablab" → http://192.168.4.1
#
# Routes :
#   GET /         → page tableau de bord
#   GET /on       → LED pleine puissance, redirect /
#   GET /off      → LED éteinte, redirect /
#   GET /dim?v=N  → LED à N% de puissance (0-100), pas de redirect
#   GET /temp     → température en texte brut (pour le JavaScript)

import network
import socket
import esp32
from machine import Pin, PWM

# --- Configuration ---
SSID    = "ESP32-Fablab"
PASSWORD = "micropython"

# --- LED en mode PWM (permet de varier la luminosité) ---
# PWM sur GPIO2, fréquence 1000 Hz
# duty : 0 = éteinte, 1023 = pleine puissance
led = PWM(Pin(2), freq=1000)
led.duty(0)
luminosite  = 100   # luminosité mémorisée en % (pour le bouton "Allumer")
led_allumee = False

# --- Point d'accès WiFi ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)
print("Réseau WiFi :", SSID)
print("Adresse IP  :", ap.ifconfig()[0])


def pct_to_duty(pct):
    """Convertit un pourcentage (0-100) en valeur PWM (0-1023)."""
    return int(max(0, min(100, pct)) * 1023 / 100)


def get_temp():
    """Retourne la température du processeur en °C."""
    return f"{(esp32.raw_temperature() - 32) / 1.8:.1f}"


def page_html(led_allumee, luminosite):
    """Génère la page tableau de bord."""
    etat   = "ALLUMÉE"  if led_allumee else "ÉTEINTE"
    couleur = "#22c55e" if led_allumee else "#374151"
    glow    = "0 0 20px #22c55e88, 0 0 40px #22c55e33" if led_allumee else "none"
    temp   = get_temp()

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>ESP32 Fablab</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      background: #0f0f1a;
      color: #e2e8f0;
      padding: 20px 16px 40px;
      max-width: 400px;
      margin: 0 auto;
    }}
    header {{
      text-align: center;
      padding: 20px 0 24px;
      border-bottom: 1px solid #1e293b;
      margin-bottom: 20px;
    }}
    header h1 {{
      font-size: 0.9rem;
      color: #38bdf8;
      letter-spacing: 3px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    header p {{ color: #475569; font-size: 0.75rem; margin-top: 4px; }}

    .card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 18px;
      padding: 22px 20px;
      margin-bottom: 14px;
    }}
    .card-label {{
      font-size: 0.65rem;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      margin-bottom: 16px;
    }}

    /* --- Carte LED --- */
    .led-row {{
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 18px;
    }}
    .led-orb {{
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: {couleur};
      box-shadow: {glow};
      flex-shrink: 0;
      transition: background 0.3s, box-shadow 0.3s;
    }}
    .led-info {{ flex: 1; }}
    .led-etat {{
      font-size: 1.1rem;
      font-weight: 700;
      color: {'#22c55e' if led_allumee else '#64748b'};
    }}
    .led-sub {{ font-size: 0.72rem; color: #475569; margin-top: 2px; }}

    .btns {{ display: flex; gap: 10px; }}
    .btn {{
      flex: 1;
      display: block;
      padding: 12px;
      border-radius: 12px;
      font-size: 0.95rem;
      font-weight: 700;
      text-decoration: none;
      text-align: center;
    }}
    .btn:active {{ opacity: 0.75; }}
    .btn-on  {{ background: #22c55e; color: #fff; }}
    .btn-off {{ background: #ef4444; color: #fff; }}

    /* --- Slider luminosité --- */
    .slider-row {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 6px;
    }}
    .slider-row input {{
      flex: 1;
      accent-color: #f59e0b;
      height: 6px;
    }}
    .slider-val {{
      font-size: 1rem;
      font-weight: 700;
      color: #f59e0b;
      width: 42px;
      text-align: right;
    }}
    .slider-labels {{
      display: flex;
      justify-content: space-between;
      font-size: 0.65rem;
      color: #475569;
      margin-top: 4px;
    }}

    /* --- Carte température --- */
    .temp-row {{
      display: flex;
      align-items: baseline;
      gap: 6px;
    }}
    .temp-val {{
      font-size: 2.4rem;
      font-weight: 800;
      color: #38bdf8;
      line-height: 1;
    }}
    .temp-unit {{ font-size: 1rem; color: #64748b; }}
    .temp-sub  {{ font-size: 0.72rem; color: #475569; margin-top: 6px; }}

    footer {{
      text-align: center;
      color: #1e293b;
      font-size: 0.7rem;
      margin-top: 24px;
      font-family: monospace;
    }}
  </style>
</head>
<body>

  <header>
    <h1>ESP32 · Fablab Ardèche</h1>
    <p>Serveur web embarqué · 192.168.4.1</p>
  </header>

  <!-- Contrôle LED -->
  <div class="card">
    <div class="card-label">Contrôle LED · GPIO 2</div>
    <div class="led-row">
      <div class="led-orb" id="orb"></div>
      <div class="led-info">
        <div class="led-etat" id="etat">LED {etat}</div>
        <div class="led-sub">Résistance 220Ω</div>
      </div>
    </div>
    <div class="btns">
      <a href="/on"  class="btn btn-on" >Allumer</a>
      <a href="/off" class="btn btn-off">Éteindre</a>
    </div>
  </div>

  <!-- Luminosité (PWM) -->
  <div class="card">
    <div class="card-label">Luminosité · PWM</div>
    <div class="slider-row">
      <input type="range" id="slider" min="0" max="100" value="{luminosite}">
      <div class="slider-val"><span id="pct">{luminosite}</span>%</div>
    </div>
    <div class="slider-labels">
      <span>Éteint</span>
      <span>Pleine puissance</span>
    </div>
  </div>

  <!-- Température -->
  <div class="card">
    <div class="card-label">Température · Processeur interne</div>
    <div class="temp-row">
      <div class="temp-val" id="temp">{temp}</div>
      <div class="temp-unit">°C</div>
    </div>
    <div class="temp-sub">Mise à jour toutes les 3 secondes</div>
  </div>

  <footer>MicroPython · ESP32 · Fablab Ardèche</footer>

  <script>
    var slider = document.getElementById('slider');
    var pct    = document.getElementById('pct');

    // Mise à jour de l'affichage en temps réel pendant le glissement
    slider.oninput = function() {{
      pct.textContent = this.value;
    }};

    // Envoi de la valeur à l'ESP32 quand le doigt se lève
    slider.onchange = function() {{
      var v = this.value;
      pct.textContent = v;
      fetch('/dim?v=' + v).catch(function() {{}});
    }};

    // Température live toutes les 3 secondes
    setInterval(function() {{
      fetch('/temp')
        .then(function(r) {{ return r.text(); }})
        .then(function(v) {{ document.getElementById('temp').textContent = v; }})
        .catch(function() {{}});
    }}, 3000);
  </script>

</body>
</html>"""


# --- Serveur web ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # libère le port si déjà utilisé
s.bind(("", 80))
s.listen(5)
print("Serveur démarré — http://192.168.4.1")

while True:
    conn, addr = s.accept()
    request = conn.recv(1024).decode()
    ligne   = request.split('\r\n')[0]   # première ligne uniquement

    if "GET /on" in ligne:
        led.duty(pct_to_duty(luminosite))
        led_allumee = True
        print("LED allumée")
        conn.send("HTTP/1.1 303 See Other\r\nLocation: /\r\nConnection: close\r\n\r\n")

    elif "GET /off" in ligne:
        led.duty(0)
        led_allumee = False
        print("LED éteinte")
        conn.send("HTTP/1.1 303 See Other\r\nLocation: /\r\nConnection: close\r\n\r\n")

    elif "GET /dim" in ligne:
        # Extraire la valeur : "GET /dim?v=75 HTTP/1.1" → 75
        try:
            v = int(ligne.split("v=")[1].split(" ")[0])
            v = max(0, min(100, v))
            luminosite  = v
            led_allumee = (v > 0)
            led.duty(pct_to_duty(v))
            print(f"Luminosité : {v}%")
        except Exception:
            pass
        conn.send("HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n")

    elif "GET /temp" in ligne:
        t = get_temp()
        conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n{t}")

    elif "GET / " in ligne:
        html = page_html(led_allumee, luminosite)
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
        conn.send(html)

    else:
        conn.send("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")

    conn.close()
