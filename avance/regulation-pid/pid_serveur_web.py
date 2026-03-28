# Régulation PID + Tableau de bord web — ESP32
# Fablab Ardèche — Cours avancé
# -----------------------------------------------------------------------
# Combine la régulation PID de température avec un serveur web
# qui affiche en temps réel : consigne, mesure, commande, courbe.
#
# Dual core :
#   Cœur 1 (thread) : régulation PID en continu (mesure + commande)
#   Cœur 0 (principal) : serveur web (dashboard smartphone)
#
# Câblage : identique à pid_temperature.py
#   GPIO26 → Gate MOSFET (PWM chauffe)
#   GPIO27 → DATA DS18B20 (+ pull-up 4,7 kΩ)
# -----------------------------------------------------------------------

import network
import socket
import _thread
from machine import Pin, PWM
from onewire import OneWire
from ds18x20 import DS18X20
from time import sleep_ms, ticks_ms, ticks_diff

# --- Matériel ---
chauffe = PWM(Pin(26), freq=1000)
chauffe.duty(0)

ds = DS18X20(OneWire(Pin(27)))
roms = ds.scan()
if not roms:
    print("ERREUR : DS18B20 non trouvé")
    raise SystemExit
capteur = roms[0]

# --- Configuration ---
SSID     = "ESP32-PID"
PASSWORD = "micropython"

# --- Paramètres PID (modifiables depuis le web) ---
pid = {
    "consigne": 40.0,
    "Kp": 50.0,
    "Ki": 0.5,
    "Kd": 20.0,
    "mesure": 0.0,
    "commande": 0,
    "erreur": 0.0,
    "actif": True,
    # Historique pour le graphique (60 derniers points)
    "historique_mesure": [],
    "historique_consigne": [],
}

ANTI_WINDUP = 500.0
somme_erreurs = 0.0
erreur_prec = 0.0


# =====================================================================
# CŒUR 1 (thread) : régulation PID en continu
# =====================================================================
def tache_pid():
    global somme_erreurs, erreur_prec

    while True:
        if not pid["actif"]:
            chauffe.duty(0)
            sleep_ms(1000)
            continue

        # Lire température
        ds.convert_temp()
        sleep_ms(750)
        mesure = ds.read_temp(capteur)
        pid["mesure"] = round(mesure, 1)

        # Calcul PID
        erreur = pid["consigne"] - mesure

        P = pid["Kp"] * erreur

        somme_erreurs += erreur
        somme_erreurs = max(-ANTI_WINDUP, min(ANTI_WINDUP, somme_erreurs))
        I = pid["Ki"] * somme_erreurs

        D = pid["Kd"] * (erreur - erreur_prec)
        erreur_prec = erreur

        commande = max(0, min(1023, int(P + I + D)))
        chauffe.duty(commande)

        pid["commande"] = commande
        pid["erreur"] = round(erreur, 1)

        # Historique (garder 60 points)
        pid["historique_mesure"].append(pid["mesure"])
        pid["historique_consigne"].append(pid["consigne"])
        if len(pid["historique_mesure"]) > 60:
            pid["historique_mesure"].pop(0)
            pid["historique_consigne"].pop(0)

        sleep_ms(250)


_thread.start_new_thread(tache_pid, ())

# --- WiFi ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)
print(f"WiFi : {SSID}  |  IP : {ap.ifconfig()[0]}")


# =====================================================================
# Page HTML avec graphique SVG
# =====================================================================
def page_html():
    d = pid
    pct = int(d["commande"] * 100 / 1023)
    etat = "ACTIF" if d["actif"] else "ARRÊTÉ"
    couleur_etat = "#22c55e" if d["actif"] else "#ef4444"

    # Construire la courbe SVG (60 points, largeur 300, hauteur 100)
    mesures = d["historique_mesure"]
    consignes = d["historique_consigne"]
    if len(mesures) > 1:
        t_min = min(min(mesures), min(consignes)) - 2
        t_max = max(max(mesures), max(consignes)) + 2
        if t_max - t_min < 5:
            t_max = t_min + 5
        # Points SVG pour la mesure
        pts_m = ' '.join(f"{i * 300 // (len(mesures)-1)},{int(100 - (m - t_min) * 100 / (t_max - t_min))}" for i, m in enumerate(mesures))
        # Ligne de consigne
        pts_c = ' '.join(f"{i * 300 // (len(consignes)-1)},{int(100 - (c - t_min) * 100 / (t_max - t_min))}" for i, c in enumerate(consignes))
        svg = f"""<svg viewBox="0 0 300 100" class="graph">
          <polyline points="{pts_c}" fill="none" stroke="#f59e0b44" stroke-width="1" stroke-dasharray="4"/>
          <polyline points="{pts_m}" fill="none" stroke="#38bdf8" stroke-width="2"/>
        </svg>
        <div class="graph-legend">
          <span style="color:#38bdf8">— Mesure</span>
          <span style="color:#f59e0b">--- Consigne</span>
          <span class="graph-range">{t_min:.0f}°C — {t_max:.0f}°C</span>
        </div>"""
    else:
        svg = '<div style="color:#475569;text-align:center;padding:20px;">En attente de données...</div>'

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="2">
  <link rel="icon" href="data:,">
  <title>PID — ESP32</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: sans-serif; background: #0f0f1a; color: #e2e8f0;
           padding: 20px 16px; max-width: 400px; margin: 0 auto; }}
    h1 {{ color: #38bdf8; font-size: 0.85rem; letter-spacing: 3px;
         text-align: center; margin-bottom: 4px; }}
    .sub {{ color: #475569; font-size: 0.7rem; text-align: center; margin-bottom: 20px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 14px;
             padding: 14px 10px; text-align: center; }}
    .card.wide {{ grid-column: span 2; }}
    .label {{ color: #64748b; font-size: 0.6rem; text-transform: uppercase;
              letter-spacing: 1.5px; margin-bottom: 6px; }}
    .val {{ font-size: 1.6rem; font-weight: 800; line-height: 1; }}
    .unit {{ font-size: 0.7rem; color: #64748b; }}
    .cyan {{ color: #38bdf8; }}
    .green {{ color: #22c55e; }}
    .orange {{ color: #f59e0b; }}
    .rose {{ color: #f472b6; }}
    .graph {{ width: 100%; height: 80px; margin-top: 8px; background: #0f172a;
              border-radius: 8px; }}
    .graph-legend {{ display: flex; justify-content: space-between;
                     font-size: 0.6rem; color: #475569; margin-top: 4px; }}
    .graph-range {{ color: #334155; }}
    .bar {{ height: 6px; background: #334155; border-radius: 3px; margin-top: 8px; }}
    .bar-fill {{ height: 100%; background: #f59e0b; border-radius: 3px;
                 width: {pct}%; transition: width 0.5s; }}
    .btns {{ display: flex; gap: 8px; margin-top: 12px; }}
    .btn {{ flex: 1; display: block; padding: 10px; border-radius: 10px;
            font-size: 0.85rem; font-weight: 700; text-decoration: none;
            text-align: center; }}
    .btn:active {{ opacity: 0.7; }}
    .btn-up {{ background: #ef4444; color: #fff; }}
    .btn-down {{ background: #3b82f6; color: #fff; }}
    .btn-toggle {{ background: {couleur_etat}; color: #fff; }}
  </style>
</head>
<body>
  <h1>RÉGULATION PID</h1>
  <p class="sub">ESP32 dual core · {etat}</p>

  <div class="grid">
    <div class="card">
      <div class="label">Consigne</div>
      <div class="val orange">{d['consigne']:.1f}<span class="unit"> °C</span></div>
    </div>
    <div class="card">
      <div class="label">Mesure</div>
      <div class="val cyan">{d['mesure']:.1f}<span class="unit"> °C</span></div>
    </div>
    <div class="card">
      <div class="label">Erreur</div>
      <div class="val rose">{d['erreur']:+.1f}<span class="unit"> °C</span></div>
    </div>
    <div class="card">
      <div class="label">Commande</div>
      <div class="val green">{pct}<span class="unit"> %</span></div>
    </div>
    <div class="card wide">
      <div class="label">Chauffe</div>
      <div class="bar"><div class="bar-fill"></div></div>
    </div>
    <div class="card wide">
      <div class="label">Courbe température (60 derniers points)</div>
      {svg}
    </div>
  </div>

  <div class="btns">
    <a href="/up"   class="btn btn-up"   >Consigne +1°C</a>
    <a href="/down" class="btn btn-down" >Consigne -1°C</a>
  </div>
  <div class="btns">
    <a href="/toggle" class="btn btn-toggle">{'Arrêter' if d['actif'] else 'Démarrer'}</a>
  </div>

</body>
</html>"""


# =====================================================================
# CŒUR 0 (principal) : serveur web
# =====================================================================
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", 80))
s.listen(5)
print(f"Serveur PID → http://192.168.4.1")
print(f"Consigne : {pid['consigne']}°C  |  Kp={pid['Kp']}  Ki={pid['Ki']}  Kd={pid['Kd']}")

while True:
    conn, addr = s.accept()
    request = conn.recv(1024).decode()
    ligne = request.split('\r\n')[0]

    if "GET /up" in ligne:
        pid["consigne"] += 1
        conn.send("HTTP/1.1 303 See Other\r\nLocation: /\r\nConnection: close\r\n\r\n")

    elif "GET /down" in ligne:
        pid["consigne"] -= 1
        conn.send("HTTP/1.1 303 See Other\r\nLocation: /\r\nConnection: close\r\n\r\n")

    elif "GET /toggle" in ligne:
        pid["actif"] = not pid["actif"]
        if not pid["actif"]:
            chauffe.duty(0)
        conn.send("HTTP/1.1 303 See Other\r\nLocation: /\r\nConnection: close\r\n\r\n")

    elif "GET / " in ligne:
        html = page_html()
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
        for i in range(0, len(html), 512):
            conn.send(html[i:i + 512])

    else:
        conn.send("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")

    conn.close()
