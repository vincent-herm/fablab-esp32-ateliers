# Atelier 02 — E-paper — Bonus ESP-NOW — Manip 03 : le récepteur (écran e-paper)
# Fablab Ardèche — MicroPython
#
# La carte T5 reçoit le nombre envoyé par l'émetteur et l'affiche en gros
# sur l'écran e-paper, avec la force du signal.
#
# Au démarrage, l'écran affiche l'ADRESSE MAC de cette carte : c'est elle
# qu'il faut recopier dans l'émetteur (manip 02).
#
# Petit défi de conception : l'écran met ~2 s à se rafraîchir, pendant que
# le bouton peut être pressé 5 fois. Le programme ne dessine donc que le
# DERNIER nombre reçu, et jamais plus d'un affichage toutes les 3 secondes.
# Comme l'émetteur envoie le total (et pas « +1 »), un message perdu ou
# sauté ne fausse rien.
#
# Matériel : carte LilyGo T5 V2.3 (écran e-paper déjà câblé)

import network
import espnow
import time
from gdeh0213b73 import init_epd, ROTATION_90
import framebuf

DELAI_MINI = 3000                       # ms minimum entre deux rafraîchissements

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
mac = ":".join("{:02x}".format(o) for o in wifi.config("mac"))
print("Adresse MAC de cette carte :", mac)


def big_text(epd, s, x, y, scale=2, c=1):
    w = len(s) * 8
    buf = bytearray(((w + 7) // 8) * 8)
    fb = framebuf.FrameBuffer(buf, w, 8, framebuf.MONO_HLSB)
    fb.fill(0)
    fb.text(s, 0, 0, 1)
    for ty in range(8):
        for tx in range(w):
            if fb.pixel(tx, ty):
                epd.fill_rect(x + tx * scale, y + ty * scale, scale, scale, c)


def texte_centre(epd, s, y, scale=2, c=1):
    largeur = len(s) * 8 * scale
    big_text(epd, s, (epd.width - largeur) // 2, y, scale, c)


def echelle_max(epd, s, maxi=8):
    """Plus grand agrandissement qui tient dans la largeur de l'écran."""
    scale = maxi
    while scale > 1 and len(s) * 8 * scale > epd.width - 16:
        scale -= 1
    return scale


def afficher_attente(epd):
    epd.fill(0)
    epd.rect(0, 0, epd.width, epd.height, 1)
    texte_centre(epd, "En attente", 20, scale=3)
    epd.text("Adresse de cette carte :", 10, 70, 1)
    texte_centre(epd, mac, 88, scale=1)
    epd.update()


def afficher_nombre(epd, nombre, rssi):
    epd.fill(0)
    epd.rect(0, 0, epd.width, epd.height, 1)
    echelle = echelle_max(epd, nombre)
    texte_centre(epd, nombre, 20 + (64 - 8 * echelle) // 2, scale=echelle)
    if rssi is not None:
        epd.text("signal : {} dBm".format(rssi), 10, 108, 1)
    epd.update()


# On ne met PAS l'écran en deep_sleep entre deux affichages : il faudrait le
# réveiller avec un reset matériel.
epd = init_epd(rotation=ROTATION_90)
afficher_attente(epd)

e = espnow.ESPNow()
e.active(True)
print("Récepteur prêt.")

affiche = None                          # ce qui est actuellement à l'écran
en_attente = None                       # dernier nombre reçu, pas encore affiché
rssi = None
dernier_rafraichissement = time.ticks_ms()

while True:
    hote, msg = e.recv(200)             # attend 200 ms au plus
    while hote is not None:             # on lit TOUT ce qui est arrivé : seul le dernier compte
        en_attente = msg.decode()
        try:
            rssi = e.peers_table[hote][0]
        except (KeyError, IndexError):
            rssi = None
        print("Reçu :", en_attente, "| signal :", rssi)
        hote, msg = e.recv(0)

    if en_attente is not None and en_attente != affiche:
        if time.ticks_diff(time.ticks_ms(), dernier_rafraichissement) >= DELAI_MINI:
            afficher_nombre(epd, en_attente, rssi)
            affiche = en_attente
            dernier_rafraichissement = time.ticks_ms()
