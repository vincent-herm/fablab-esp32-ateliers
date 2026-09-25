# Atelier 02 — E-paper — Bonus ESP-NOW — Manip 01 : l'adresse MAC de ta carte
# Fablab Ardèche — MicroPython
#
# Chaque carte ESP32 a une adresse unique, gravée en usine : l'adresse MAC.
# C'est elle qui permet à une carte d'en trouver une autre, comme un numéro
# de téléphone. ESP-NOW s'en sert pour envoyer un message à UNE carte précise.
#
# Lance ce programme sur chaque carte et note son adresse.
#
# Matériel : n'importe quelle carte ESP32, rien à brancher

import network

wifi = network.WLAN(network.STA_IF)
wifi.active(True)                       # la radio doit être allumée pour lire l'adresse

mac = wifi.config("mac")                # 6 octets
texte = ":".join("{:02x}".format(o) for o in mac)

print("Adresse MAC de cette carte :", texte)
