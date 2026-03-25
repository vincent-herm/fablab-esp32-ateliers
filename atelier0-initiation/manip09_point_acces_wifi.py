# Manipulation 09 — L'ESP32 crée son propre réseau WiFi
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# L'ESP32 peut fonctionner comme un routeur WiFi miniature.
# On l'appelle alors "Access Point" (AP) ou "Point d'accès".
#
# Une fois ce code lancé :
#   1. Prendre son smartphone
#   2. Aller dans les réglages WiFi
#   3. Le réseau "ESP32-Polinno" apparaît dans la liste
#   4. Se connecter avec le mot de passe : micropython
#   5. L'ESP32 distribue automatiquement une adresse IP : 192.168.4.x
#
# C'est exactement ce que fait votre box internet à la maison,
# en beaucoup plus petit et pour beaucoup moins cher.
#
# Rien à brancher.
# -----------------------------------------------------------------------

import network    # module WiFi
import time       # pour les pauses

# Nom du réseau WiFi que l'ESP32 va créer
SSID     = "ESP32-Polinno"
PASSWORD = "micropython"

# Créer une interface WiFi en mode "Access Point"
ap = network.WLAN(network.AP_IF)
ap.active(True)    # activer le module WiFi en mode AP

# Configurer le nom et le mot de passe du réseau
ap.config(essid=SSID, password=PASSWORD)

# Attendre que le réseau soit opérationnel
while not ap.active():
    time.sleep(0.1)

# Lire la configuration réseau attribuée automatiquement
# ifconfig() retourne : (adresse_ip, masque, passerelle, dns)
ip, masque, passerelle, dns = ap.ifconfig()

print("=" * 40)
print("Réseau WiFi créé !")
print(f"  Nom (SSID)  : {SSID}")
print(f"  Mot de passe: {PASSWORD}")
print(f"  Adresse IP  : {ip}")
print("=" * 40)
print()
print("Connectez votre smartphone à ce réseau.")
print("L'ESP32 est accessible à l'adresse :", ip)
print()
print("Ce programme tourne indéfiniment.")
print("Appuyer Ctrl+C pour arrêter.")

# Le réseau reste actif tant que le programme tourne
while True:
    time.sleep(1)

# -----------------------------------------------------------------------
# À RETENIR :
#   - network.AP_IF  = mode Access Point (crée un réseau)
#   - network.STA_IF = mode Station (rejoint un réseau existant)
#   - ap.config()    = configure le nom et le mot de passe
#   - ap.ifconfig()  = retourne les infos réseau (IP, masque, etc.)
#   - L'adresse IP de l'AP est toujours 192.168.4.1 par défaut
#
# DANS LE SHELL :
#   >>> ap.isconnected()    # vérifie si des appareils sont connectés
#   >>> ap.status()         # retourne l'état de l'interface
# -----------------------------------------------------------------------
