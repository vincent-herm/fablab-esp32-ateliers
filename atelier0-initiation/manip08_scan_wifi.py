# Manipulation 08 — Scanner les réseaux WiFi environnants
# Fablab Ardèche — Atelier d'initiation
# -----------------------------------------------------------------------
# L'ESP32 est équipé d'une antenne WiFi intégrée.
# Il peut se connecter à un réseau existant (mode Station / STA)
# ou créer son propre réseau (mode Access Point / AP).
#
# Dans cette manip, on utilise le mode Station juste pour écouter :
# on cherche les réseaux WiFi disponibles dans la salle.
# Chaque réseau trouvé affiche son nom (SSID) et son niveau de signal.
#
# Le signal WiFi se mesure en dBm (décibels milliwatts) :
#   -30 dBm → signal excellent (très près du routeur)
#   -70 dBm → signal faible
#   -90 dBm → signal limite
#
# Rien à brancher.
# -----------------------------------------------------------------------

import network    # module pour tout ce qui concerne le WiFi et les réseaux
import time       # pour les pauses

# Créer une interface WiFi en mode "Station" (client, pas serveur)
wifi = network.WLAN(network.STA_IF)
wifi.active(True)    # activer le module WiFi

print("Scan des réseaux WiFi en cours...")
print()

# scan() retourne une liste de tuples :
# (ssid, bssid, canal, signal, securite, cache)
reseaux = wifi.scan()

print(f"{len(reseaux)} réseaux trouvés :")
print("-" * 40)

for reseau in reseaux:
    nom    = reseau[0].decode("utf-8")  # nom du réseau (bytes → texte)
    signal = reseau[3]                  # niveau de signal en dBm
    canal  = reseau[2]                  # numéro de canal WiFi (1 à 13)

    # Barre de signal visuelle (de 0 à 5 barres)
    force = max(0, min(5, (signal + 100) // 10))
    barres = "█" * force + "░" * (5 - force)

    print(f"  {barres}  {signal:4d} dBm  canal {canal:2d}  {nom}")

print()
print("Scan terminé.")

# -----------------------------------------------------------------------
# À RETENIR :
#   - network.WLAN() crée une interface WiFi
#   - network.STA_IF = mode Station (se connecte à un réseau existant)
#   - network.AP_IF  = mode Access Point (crée son propre réseau)
#   - scan() retourne une liste de tuples avec les infos de chaque réseau
#   - .decode("utf-8") convertit des bytes en texte lisible
# -----------------------------------------------------------------------
