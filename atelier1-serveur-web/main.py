# Atelier 01 — Serveur web avec ESP32
# Fablab Ardèche — MicroPython
#
# L'ESP32 crée son propre réseau WiFi et sert une page HTML
# pour contrôler une LED depuis un navigateur.
#
# Matériel : ESP32, LED sur GPIO2, résistance 220Ω
# Connexion : rejoindre le WiFi "ESP32-Fablab" → http://192.168.4.1

import network
import socket
from machine import Pin

# --- Configuration ---
SSID     = "ESP32-Fablab"
PASSWORD = "micropython"
LED_PIN  = 2

# --- Initialisation ---
led = Pin(LED_PIN, Pin.OUT)
led.off()

# Créer un point d'accès WiFi
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)
print("Réseau WiFi créé :", SSID)
print("Adresse IP :", ap.ifconfig()[0])

# --- Page HTML ---
def page_html(led_allumee):
    etat  = "ON" if led_allumee else "OFF"
    color = "#22c55e" if led_allumee else "#ef4444"
    btn_on  = "disabled" if led_allumee else ""
    btn_off = "disabled" if not led_allumee else ""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ESP32 Fablab</title>
  <style>
    body {{ font-family: sans-serif; text-align: center; background: #111; color: #eee; padding: 40px; }}
    h1   {{ font-size: 2rem; margin-bottom: 8px; }}
    .etat {{ font-size: 1.5rem; font-weight: bold; color: {color}; margin: 24px 0; }}
    .btn  {{ display: inline-block; padding: 14px 32px; margin: 8px;
             font-size: 1.1rem; border: none; border-radius: 8px; cursor: pointer; }}
    .on   {{ background: #22c55e; color: #fff; }}
    .off  {{ background: #ef4444; color: #fff; }}
    .btn:disabled {{ opacity: 0.4; cursor: default; }}
  </style>
</head>
<body>
  <h1>💡 Contrôle LED</h1>
  <p>ESP32 Fablab Ardèche</p>
  <div class="etat">LED : {etat}</div>
  <form method="GET">
    <button class="btn on"  name="led" value="on"  {btn_on} >Allumer</button>
    <button class="btn off" name="led" value="off" {btn_off}>Éteindre</button>
  </form>
</body>
</html>"""

# --- Serveur web ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("", 80))
s.listen(5)
print("Serveur démarré — http://192.168.4.1")

while True:
    conn, addr = s.accept()
    request = conn.recv(1024).decode()

    # Lire la commande dans l'URL (?led=on ou ?led=off)
    if "?led=on" in request:
        led.on()
    elif "?led=off" in request:
        led.off()

    # Envoyer la page
    html = page_html(led.value() == 1)
    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
    conn.send(html)
    conn.close()
