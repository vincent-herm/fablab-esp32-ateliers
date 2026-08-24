# relais_web.py — 2 relais pilotés via serveur web (WiFi maison)
# -----------------------------------------------------------------------
# Relais 1 → Pin 27    Relais 2 → Pin 14
# L'ESP32 se connecte à ta box → ouvre l'IP sur smartphone
# -----------------------------------------------------------------------

import network
import socket
from machine import Pin
from time import sleep_ms

# ── À modifier ──────────────────────────────────────────────────────────
SSID      = "NOM_DE_TON_WIFI"
PASSWORD  = "MOT_DE_PASSE_WIFI"
ACTIF_BAS = True   # True = module relais bleu (LOW=ON)
# ────────────────────────────────────────────────────────────────────────

r1 = Pin(27, Pin.OUT)
r2 = Pin(14, Pin.OUT)

def set_relais(pin, on):
    pin.value((0 if on else 1) if ACTIF_BAS else (1 if on else 0))

set_relais(r1, False)
set_relais(r2, False)
e1 = e2 = False

# ── Connexion WiFi ──────────────────────────────────────────────────────
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)
print(f"Connexion à {SSID}...")
for _ in range(20):
    if wifi.isconnected():
        break
    sleep_ms(500)
    print(".", end="")

if not wifi.isconnected():
    print("\nErreur WiFi — vérifie SSID et PASSWORD")
    raise SystemExit

ip = wifi.ifconfig()[0]
print(f"\nConnecté !  →  http://{ip}")
print("Ouvre cette adresse sur ton smartphone")

# ── Page HTML ───────────────────────────────────────────────────────────
def page_html():
    s1 = "ON"  if e1 else "OFF"
    s2 = "ON"  if e2 else "OFF"
    c1 = "#2ecc71" if e1 else "#e74c3c"
    c2 = "#2ecc71" if e2 else "#e74c3c"
    l1 = "Éteindre R1" if e1 else "Allumer R1"
    l2 = "Éteindre R2" if e2 else "Allumer R2"
    a1 = "off" if e1 else "on"
    a2 = "off" if e2 else "on"

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Relais ESP32</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:Arial,sans-serif;background:#1a1a2e;color:#fff;padding:20px;text-align:center}}
  h1{{font-size:1.6em;margin:20px 0 30px}}
  .card{{background:#16213e;border-radius:20px;padding:28px 20px;margin:0 auto 20px;max-width:360px}}
  .label{{font-size:0.9em;color:#aaa;margin-bottom:8px}}
  .etat{{font-size:2.6em;font-weight:bold;margin:8px 0 20px}}
  .btn{{display:block;background:#0f3460;color:#fff;text-decoration:none;
        padding:18px;border-radius:14px;font-size:1.2em;font-weight:bold;
        border:2px solid #ffffff22}}
  .btn:active{{background:#e94560}}
  .ip{{color:#555;font-size:0.75em;margin-top:30px}}
</style>
</head><body>
<h1>⚡ Relais ESP32</h1>

<div class="card">
  <div class="label">RELAIS 1 — Pin 27</div>
  <div class="etat" style="color:{c1}">{s1}</div>
  <a class="btn" href="/r1/{a1}">{l1}</a>
</div>

<div class="card">
  <div class="label">RELAIS 2 — Pin 14</div>
  <div class="etat" style="color:{c2}">{s2}</div>
  <a class="btn" href="/r2/{a2}">{l2}</a>
</div>

<div class="ip">ESP32 · {ip}</div>
</body></html>"""

# ── Serveur HTTP ─────────────────────────────────────────────────────────
srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(socket.getaddrinfo("0.0.0.0", 80)[0][-1])
srv.listen(1)
print("Serveur prêt.\n")

while True:
    try:
        conn, addr = srv.accept()
        req   = conn.recv(1024).decode()
        route = req.split("\r\n")[0].split(" ")[1] if req else "/"

        if   route == "/r1/on":  set_relais(r1, True);  e1 = True;  print("R1 ON")
        elif route == "/r1/off": set_relais(r1, False); e1 = False; print("R1 OFF")
        elif route == "/r2/on":  set_relais(r2, True);  e2 = True;  print("R2 ON")
        elif route == "/r2/off": set_relais(r2, False); e2 = False; print("R2 OFF")

        if route in ("/r1/on", "/r1/off", "/r2/on", "/r2/off"):
            conn.send(b"HTTP/1.1 303 See Other\r\nLocation: /\r\nContent-Length: 0\r\n\r\n")
        else:
            html = page_html()
            conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(html)}\r\n\r\n{html}")
    except OSError:
        pass
    finally:
        conn.close()
