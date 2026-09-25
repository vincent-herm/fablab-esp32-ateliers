# Atelier 02 — E-paper — Bonus ESP-NOW — Manip 02 : l'émetteur (bouton qui compte)
# Fablab Ardèche — MicroPython
#
# À chaque appui sur le bouton, la carte ajoute 1 à un compteur et envoie le
# NOMBRE TOTAL à l'autre carte par ESP-NOW, sans box ni WiFi.
#
# La LED de la carte donne le résultat de l'envoi :
#   - allumée 0,2 s : l'autre carte a bien accusé réception
#   - clignote 3 fois : personne n'a répondu (mauvaise adresse ? trop loin ?)
#
# Matériel : carte ESP32 simple + 1 bouton poussoir
# Connexions : bouton entre GPIO5 et GND, LED intégrée sur GPIO2
#
# COMMENT UTILISER :
#   1. Lance d'abord le récepteur (manip 03) : son écran affiche son adresse
#   2. Recopie cette adresse dans MAC_RECEPTEUR ci-dessous
#   3. Lance ce programme, puis appuie sur le bouton

import network
import espnow
import time
from machine import Pin
import ubinascii

MAC_RECEPTEUR = "24:6f:28:b1:e4:2c"     # à remplacer par l'adresse affichée par le récepteur

bp = Pin(5, Pin.IN, Pin.PULL_UP)        # bouton : 0 = appuyé
led = Pin(2, Pin.OUT)

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

e = espnow.ESPNow()
e.active(True)
adresse = ubinascii.unhexlify(MAC_RECEPTEUR.replace(":", ""))
e.add_peer(adresse)

compteur = 0
print("Radio ESP-NOW activée, envoi vers", MAC_RECEPTEUR)
print("Prêt. Appuie sur le bouton.")

while True:
    if bp.value() == 0:
        compteur += 1
        try:
            recu = e.send(adresse, str(compteur))   # True si l'autre carte a répondu
        except OSError as erreur:                   # l'erreur s'affiche au lieu d'arrêter le programme
            print("Erreur d'envoi :", erreur)
            recu = False
        if recu:
            print(compteur, "→ reçu")
            led.value(1)
            time.sleep_ms(200)
            led.value(0)
        else:
            print(compteur, "→ PAS de réponse")
            for _ in range(3):
                led.value(1)
                time.sleep_ms(100)
                led.value(0)
                time.sleep_ms(100)
        time.sleep_ms(30)                        # anti-rebond
        while bp.value() == 0:                   # attendre le relâchement
            time.sleep_ms(10)
        time.sleep_ms(30)
    time.sleep_ms(10)
