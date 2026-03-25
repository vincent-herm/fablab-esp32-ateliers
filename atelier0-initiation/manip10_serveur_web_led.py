# Manipulation 10 — Contrôler la LED depuis son smartphone (serveur web)
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# C'est la manipulation finale — le grand "Wow" de l'atelier.
#
# Ce programme combine tout ce qu'on a vu :
#   - L'ESP32 crée son propre réseau WiFi (manip 09)
#   - Il démarre un serveur web sur ce réseau (comme un mini-site internet)
#   - Il sert une page HTML avec deux boutons : Allumer / Éteindre
#   - Quand on appuie sur un bouton depuis le téléphone, la LED réagit
#
# COMMENT UTILISER :
#   1. Lancer ce programme dans Thonny
#   2. Sur le smartphone : aller dans les réglages WiFi
#   3. Se connecter au réseau "ESP32-Polinno" (mot de passe : micropython)
#   4. Ouvrir le navigateur et taper : 192.168.4.1
#   5. La page de contrôle apparaît → appuyer sur les boutons
#
# Rien à brancher — LED intégrée sur GPIO 2.
# -----------------------------------------------------------------------

import network    # module WiFi
import socket     # module réseau bas niveau (créer un serveur TCP/IP)
from machine import Pin    # pour contrôler la LED

# --- Configuration ---
SSID     = "ESP32-Polinno"
PASSWORD = "micropython"
LED_PIN  = 2               # GPIO 2 = LED intégrée sur toutes les ESP32

# --- Initialisation de la LED ---
led = Pin(LED_PIN, Pin.OUT)
led.off()    # éteindre la LED au démarrage

# --- Création du point d'accès WiFi ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)
print(f"Réseau WiFi créé : {SSID}")
print(f"Adresse IP       : {ap.ifconfig()[0]}")

# -----------------------------------------------------------------------
# La page HTML qui sera envoyée au navigateur du smartphone
# Elle est construite comme une chaîne de texte Python (f-string)
# et intègre directement le CSS (mise en forme) et le HTML (structure)
# -----------------------------------------------------------------------
def page_html(led_allumee):
    """Génère la page HTML en fonction de l'état de la LED."""
    etat  = "ALLUMÉE" if led_allumee else "ÉTEINTE"
    color = "#22c55e"  if led_allumee else "#ef4444"    # vert si allumée, rouge si éteinte
    desactiver_on  = "disabled" if led_allumee     else ""   # griser le bouton déjà actif
    desactiver_off = "disabled" if not led_allumee else ""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fablab Polinno — LED</title>
  <style>
    body {{
      font-family: sans-serif;
      text-align: center;
      background: #1a1a2e;
      color: #eee;
      padding: 40px 20px;
    }}
    h1   {{ font-size: 2rem; margin-bottom: 4px; }}
    .sous-titre {{ color: #aaa; margin-bottom: 32px; }}
    .etat {{
      font-size: 1.6rem;
      font-weight: bold;
      color: {color};
      margin: 28px 0;
      padding: 16px;
      border: 2px solid {color};
      border-radius: 12px;
      display: inline-block;
      min-width: 200px;
    }}
    .btn {{
      display: inline-block;
      padding: 16px 40px;
      margin: 10px;
      font-size: 1.2rem;
      font-weight: bold;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      width: 140px;
    }}
    .on  {{ background: #22c55e; color: #fff; }}
    .off {{ background: #ef4444; color: #fff; }}
    .btn:disabled {{ opacity: 0.3; cursor: default; }}
    .pied {{ margin-top: 48px; color: #555; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <h1>💡 Contrôle LED</h1>
  <p class="sous-titre">Fablab Polinno — ESP32</p>

  <div class="etat">LED : {etat}</div>

  <br>

  <!-- Formulaire GET : les boutons envoient ?led=on ou ?led=off dans l'URL -->
  <form method="GET">
    <button class="btn on"  name="led" value="on"  {desactiver_on} >Allumer</button>
    <button class="btn off" name="led" value="off" {desactiver_off}>Éteindre</button>
  </form>

  <p class="pied">ESP32 · MicroPython · Fablab Ardèche</p>
</body>
</html>"""


# -----------------------------------------------------------------------
# Démarrage du serveur web
# Un serveur web écoute sur le port 80 (le port HTTP standard)
# et attend qu'un navigateur se connecte pour lui envoyer une page.
# -----------------------------------------------------------------------
serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serveur.bind(("", 80))     # écouter sur toutes les interfaces, port 80
serveur.listen(5)          # accepter jusqu'à 5 connexions en attente

print("Serveur web démarré → http://192.168.4.1")
print("Appuyer Ctrl+C pour arrêter")
print()

# Boucle principale : attendre et traiter les requêtes HTTP
while True:
    # Attendre qu'un navigateur se connecte (bloquant)
    connexion, adresse = serveur.accept()
    print(f"Connexion depuis {adresse[0]}")

    # Lire la requête HTTP envoyée par le navigateur
    # Exemple de requête : "GET /?led=on HTTP/1.1\r\nHost: ..."
    requete = connexion.recv(1024).decode()

    # Analyser la requête pour savoir quelle commande envoyer à la LED
    if "?led=on" in requete:
        led.on()
        print("  → LED allumée")
    elif "?led=off" in requete:
        led.off()
        print("  → LED éteinte")

    # Générer et envoyer la page HTML en réponse
    html = page_html(led.value() == 1)
    connexion.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
    connexion.send(html)
    connexion.close()    # fermer la connexion après chaque requête

# -----------------------------------------------------------------------
# CE QU'ON A APPRIS DANS CET ATELIER :
#   1. Le REPL : dialogue interactif avec l'ESP32
#   2. GPIO output : contrôler une LED (allumer / éteindre)
#   3. Boucle infinie : while True + Ctrl+C
#   4. PWM : simuler une tension variable → LED qui "respire"
#   5. GPIO input : lire un bouton (logique active bas)
#   6. Automatisme simple : capteur → actionneur
#   7. Capteur interne : température du processeur
#   8. WiFi scan : détecter les réseaux environnants
#   9. Access Point : créer son propre réseau WiFi
#  10. Serveur web : servir du HTML et réagir aux commandes HTTP
#
# PROCHAINES ÉTAPES :
#   - Ajouter un capteur de température (DHT22) sur la page web
#   - Contrôler plusieurs LEDs avec des couleurs différentes
#   - Enregistrer l'historique des actions dans un fichier
# -----------------------------------------------------------------------
