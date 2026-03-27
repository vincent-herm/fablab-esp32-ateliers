# Threading — Exemple 4 : Tout en un (LED + température + web + bouton)
# Fablab Ardèche — ESP32 dual core
# -----------------------------------------------------------------------
# On combine tout sur les 2 cœurs :
#
#   Cœur 1 (thread) : LED qui respire + mesure température en continu
#   Cœur 0 (principal) : serveur web + comptage appuis bouton BOOT
#
# Chaque cœur fait DEUX choses à la fois grâce à des boucles non bloquantes.
#
# Rien à brancher — LED intégrée GPIO 2 + bouton BOOT GPIO 0.
# -----------------------------------------------------------------------

import network
import socket
import esp32
import _thread
from machine import Pin, PWM
from time import sleep_ms, ticks_ms, ticks_diff

# --- Configuration ---
SSID     = "ESP32-Polinno"
PASSWORD = "micropython"

bouton = Pin(0, Pin.IN, Pin.PULL_UP)
led    = PWM(Pin(2), freq=1000)
led.duty(0)

# --- Données partagées entre les 2 cœurs ---
import gc
donnees = {
    "temperature": 0.0,
    "nb_mesures": 0,
    "nb_appuis": 0,
    "uptime_s": 0,
    "ram_libre": 0,
    "ram_totale": 0,
}

# =====================================================================
# CŒUR 1 (thread) : LED qui respire + mesure température
# =====================================================================
def tache_capteur_et_led():
    lum = 0
    sens = 5       # pas de montée (+5) ou descente (-5)
    dernier_mesure = ticks_ms()
    t0 = ticks_ms()

    while True:
        # --- LED qui respire (non bloquant) ---
        lum += sens
        if lum >= 1023:
            lum = 1023
            sens = -5
        elif lum <= 0:
            lum = 0
            sens = 5
        led.duty(lum)

        # --- Mesures toutes les 2 secondes ---
        if ticks_diff(ticks_ms(), dernier_mesure) > 2000:
            temp_f = esp32.raw_temperature()
            donnees["temperature"] = round((temp_f - 32) / 1.8, 1)
            donnees["nb_mesures"] += 1
            donnees["uptime_s"] = ticks_diff(ticks_ms(), t0) // 1000
            gc.collect()
            donnees["ram_libre"] = gc.mem_free()
            donnees["ram_totale"] = gc.mem_free() + gc.mem_alloc()
            dernier_mesure = ticks_ms()

        sleep_ms(5)

# Lancer le thread
_thread.start_new_thread(tache_capteur_et_led, ())

# =====================================================================
# CŒUR 0 (principal) : serveur web + comptage bouton
# =====================================================================

# --- WiFi ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)
print(f"WiFi : {SSID}  |  IP : {ap.ifconfig()[0]}")

# --- Page HTML ---
def format_uptime(s):
    """Convertit des secondes en texte lisible."""
    if s < 60:
        return f"{s}s"
    elif s < 3600:
        return f"{s // 60}m {s % 60}s"
    else:
        return f"{s // 3600}h {(s % 3600) // 60}m"

def page_html():
    d = donnees
    ram_pct = int(d['ram_libre'] * 100 / d['ram_totale']) if d['ram_totale'] > 0 else 0
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
           padding: 30px 16px; text-align: center; max-width: 380px; margin: 0 auto; }}
    h1 {{ color: #38bdf8; font-size: 0.9rem; letter-spacing: 3px; margin-bottom: 4px; }}
    .sub {{ color: #475569; font-size: 0.75rem; margin-bottom: 24px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px;
             padding: 18px 12px; }}
    .card.wide {{ grid-column: span 2; }}
    .label {{ color: #64748b; font-size: 0.6rem; text-transform: uppercase;
              letter-spacing: 1.5px; margin-bottom: 8px; }}
    .val {{ font-size: 2rem; font-weight: 800; line-height: 1; }}
    .sm {{ font-size: 1.3rem; }}
    .cyan {{ color: #38bdf8; }}
    .green {{ color: #22c55e; }}
    .orange {{ color: #f59e0b; }}
    .violet {{ color: #a78bfa; }}
    .rose {{ color: #f472b6; }}
    .unit {{ font-size: 0.8rem; color: #64748b; }}
    .bar {{ height: 8px; background: #334155; border-radius: 4px; margin-top: 10px; }}
    .bar-fill {{ height: 100%; border-radius: 4px; }}
    .foot {{ color: #1e293b; font-size: 0.65rem; margin-top: 20px; }}
  </style>
</head>
<body>
  <h1>ESP32 · DUAL CORE</h1>
  <p class="sub">4 tâches en parallèle sur 2 cœurs</p>
  <div class="grid">
    <div class="card">
      <div class="label">Température</div>
      <div class="val cyan">{d['temperature']}<span class="unit"> °C</span></div>
    </div>
    <div class="card">
      <div class="label">En ligne</div>
      <div class="val violet sm">{format_uptime(d['uptime_s'])}</div>
    </div>
    <div class="card">
      <div class="label">Appuis bouton</div>
      <div class="val green">{d['nb_appuis']}</div>
    </div>
    <div class="card">
      <div class="label">Mesures</div>
      <div class="val orange">{d['nb_mesures']}</div>
    </div>
    <div class="card wide">
      <div class="label">RAM libre : {d['ram_libre'] // 1024} ko / {d['ram_totale'] // 1024} ko ({ram_pct}%)</div>
      <div class="bar"><div class="bar-fill" style="width:{ram_pct}%; background:#22c55e;"></div></div>
    </div>
  </div>
  <p class="foot">Rafraîchissement auto · 192.168.4.1</p>
</body>
</html>"""


# --- Serveur web (non bloquant grâce au timeout) ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", 80))
s.listen(5)
s.settimeout(0.1)     # timeout 100ms → ne bloque pas le bouton

print("Serveur web → http://192.168.4.1")
print("Bouton BOOT = compteur d'appuis")
print("LED respire + température en continu sur le cœur 1")
print()

etat_precedent = 1

while True:
    # --- Vérifier le bouton (non bloquant) ---
    etat = bouton.value()
    if etat_precedent == 1 and etat == 0:    # front descendant
        donnees["nb_appuis"] += 1
        print(f"Appui n°{donnees['nb_appuis']}")
    etat_precedent = etat

    # --- Serveur web (non bloquant grâce au timeout) ---
    try:
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
    except OSError:
        pass    # timeout — pas de connexion, on continue

    sleep_ms(10)

# -----------------------------------------------------------------------
# 4 TÂCHES EN PARALLÈLE SUR 2 CŒURS :
#
#   Cœur 1 (thread) :
#     ✓ LED qui respire en PWM (toutes les 5 ms)
#     ✓ Mesure température (toutes les 2 s)
#
#   Cœur 0 (principal) :
#     ✓ Serveur web (timeout 100 ms, non bloquant)
#     ✓ Comptage appuis bouton BOOT (détection de front)
#
# L'astuce : s.settimeout(0.1) rend accept() non bloquant.
# Sans ça, accept() bloquerait indéfiniment et le bouton ne
# serait jamais lu.
# -----------------------------------------------------------------------
