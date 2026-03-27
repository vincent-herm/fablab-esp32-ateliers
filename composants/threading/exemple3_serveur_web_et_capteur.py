# Threading — Exemple 3 : Serveur web + mesure en continu
# Fablab Ardèche — ESP32 dual core
# -----------------------------------------------------------------------
# L'application la plus utile du threading sur ESP32 :
#
#   Cœur 0 : serveur web qui répond aux requêtes des smartphones
#   Cœur 1 : mesure la température en continu et stocke la dernière valeur
#
# Sans threading, le serveur web BLOQUE pendant qu'il attend une connexion
# (accept() est bloquant). Impossible de mesurer quoi que ce soit en même temps.
#
# Avec threading, la mesure tourne en permanence sur l'autre cœur,
# et le serveur web lit simplement la dernière valeur mesurée.
#
# Rien à brancher — LED intégrée GPIO 2.
# -----------------------------------------------------------------------

import network
import socket
import esp32
import _thread
from machine import Pin
from time import sleep

# --- Configuration ---
SSID     = "ESP32-Polinno"
PASSWORD = "micropython"

led = Pin(2, Pin.OUT)

# --- Variable partagée entre les deux cœurs ---
# On utilise un dictionnaire pour partager les données de façon thread-safe
donnees = {
    "temperature": 0.0,
    "nb_mesures": 0,
}

# --- Thread : mesure en continu sur le cœur 1 ---
def mesurer():
    """Lit la température toutes les secondes et met à jour le dictionnaire."""
    while True:
        temp_f = esp32.raw_temperature()
        temp_c = (temp_f - 32) / 1.8
        donnees["temperature"] = round(temp_c, 1)
        donnees["nb_mesures"] += 1
        sleep(1)

# Lancer le thread de mesure
_thread.start_new_thread(mesurer, ())

# --- Point d'accès WiFi ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)
print(f"WiFi : {SSID}  |  IP : {ap.ifconfig()[0]}")


def page_html():
    temp = donnees["temperature"]
    nb   = donnees["nb_mesures"]
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="3">
  <link rel="icon" href="data:,">
  <title>ESP32 Dual Core</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: sans-serif; background: #0f0f1a; color: #e2e8f0;
           padding: 40px 20px; text-align: center; }}
    h1 {{ color: #38bdf8; font-size: 1rem; letter-spacing: 3px; margin-bottom: 8px; }}
    .sub {{ color: #475569; font-size: 0.8rem; margin-bottom: 32px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px;
             padding: 24px; margin: 0 auto 16px; max-width: 300px; }}
    .label {{ color: #64748b; font-size: 0.7rem; text-transform: uppercase;
              letter-spacing: 1px; margin-bottom: 8px; }}
    .val {{ font-size: 2.5rem; font-weight: 800; color: #38bdf8; }}
    .unit {{ color: #64748b; font-size: 1rem; }}
    .count {{ color: #a78bfa; font-size: 1.5rem; font-weight: 700; }}
    .foot {{ color: #1e293b; font-size: 0.7rem; margin-top: 24px; }}
  </style>
</head>
<body>
  <h1>ESP32 · DUAL CORE</h1>
  <p class="sub">Cœur 0 : serveur web · Cœur 1 : mesure en continu</p>
  <div class="card">
    <div class="label">Température processeur</div>
    <div class="val">{temp}<span class="unit"> °C</span></div>
  </div>
  <div class="card">
    <div class="label">Mesures effectuées</div>
    <div class="count">{nb}</div>
  </div>
  <p class="foot">Rafraîchissement automatique toutes les 3s</p>
</body>
</html>"""


# --- Serveur web sur le cœur 0 (principal) ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", 80))
s.listen(5)
print("Serveur web démarré → http://192.168.4.1")
print("La mesure tourne en continu sur le cœur 1")
print()

while True:
    conn, addr = s.accept()
    request = conn.recv(1024).decode()
    ligne = request.split('\r\n')[0]

    if "GET / " in ligne:
        html = page_html()
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
        for i in range(0, len(html), 512):
            conn.send(html[i:i + 512])
    else:
        conn.send("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")

    conn.close()

# -----------------------------------------------------------------------
# POURQUOI C'EST IMPORTANT :
#
#   Sans threading :
#     Le serveur web attend une connexion (accept = bloquant).
#     Pendant qu'il attend, rien d'autre ne tourne.
#     La température n'est lue QUE quand un client se connecte.
#
#   Avec threading :
#     La mesure tourne EN PERMANENCE sur le cœur 1 (1 mesure/seconde).
#     Le serveur web tourne sur le cœur 0.
#     Quand un client se connecte, il lit la DERNIÈRE valeur mesurée.
#     → Donnée toujours fraîche, serveur toujours réactif.
#
# C'EST LA BASE DE TOUT SYSTÈME EMBARQUÉ SÉRIEUX :
#   acquisition de données + interface utilisateur en parallèle.
# -----------------------------------------------------------------------
