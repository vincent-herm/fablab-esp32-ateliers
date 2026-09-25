# Atelier 02 — E-paper — Manip 07 : écris sur l'écran depuis ton iPhone
# Fablab Ardèche — MicroPython
#
# La carte crée son réseau WiFi et un mini site web. Depuis ton téléphone
# (iPhone ou Android), tu tapes un message : il s'affiche en gros sur
# l'écran e-paper, et y reste même quand tu débranches la carte.
#
# COMMENT UTILISER :
#   1. Choisis un NOM_RESEAU qui n'appartient qu'à toi (plusieurs cartes
#      dans la salle : sinon on ne sait plus laquelle est laquelle)
#   2. Lance ce programme dans Thonny : l'écran affiche les instructions
#   3. Téléphone : Réglages → WiFi → ton réseau (mot de passe ci-dessous)
#   4. Ouvre Safari et tape l'adresse  192.168.4.1
#   5. Écris ton message, appuie sur « Afficher »
#
# Attention : pas d'accents sur l'écran (police ASCII). Le programme les
# remplace tout seul : é → e, ç → c, etc.
#
# Matériel : carte LilyGo T5 V2.3 (écran e-paper déjà câblé)

import network
import socket
import time
from gdeh0213b73 import init_epd, ROTATION_90
import framebuf

# --- Configuration ---
NOM_RESEAU = "Ecran-Camille"          # à personnaliser
MOT_DE_PASSE = "fablab2026"           # 8 caractères minimum
DELAI_MINI = 10                       # secondes entre deux affichages
LONGUEUR_MAX = 60                     # caractères maximum par message

ACCENTS = {
    "é": "e", "è": "e", "ê": "e", "ë": "e", "à": "a", "â": "a", "ä": "a",
    "î": "i", "ï": "i", "ô": "o", "ö": "o", "ù": "u", "û": "u", "ü": "u",
    "ç": "c", "œ": "oe", "É": "E", "È": "E", "Ê": "E", "À": "A", "Ç": "C",
    "’": "'",
}


# --- Traitement du texte reçu -------------------------------------------

def decoder(s):
    """Décode le texte d'une adresse web : « Caf%C3%A9+noir » → « Café noir »."""
    s = s.replace("+", " ")
    octets = bytearray()
    i = 0
    while i < len(s):
        if s[i] == "%" and i + 2 < len(s):
            try:
                octets.append(int(s[i + 1:i + 3], 16))
                i += 3
                continue
            except ValueError:
                pass
        octets.extend(s[i].encode())
        i += 1
    try:
        return octets.decode("utf-8")
    except UnicodeError:
        return ""


def sans_accents(texte):
    """Remplace les accents, et les caractères hors ASCII par « ? »."""
    resultat = ""
    for c in texte:
        if c in ACCENTS:
            resultat += ACCENTS[c]
        elif 32 <= ord(c) < 127:
            resultat += c
        else:
            resultat += "?"
    return resultat


def couper(texte, largeur):
    """Découpe un texte en lignes de 'largeur' caractères, sans couper les mots."""
    lignes = []
    ligne = ""
    for mot in texte.split():
        while len(mot) > largeur:               # mot trop long : on le tronçonne
            if ligne:
                lignes.append(ligne)
                ligne = ""
            lignes.append(mot[:largeur])
            mot = mot[largeur:]
        if not mot:
            continue
        if not ligne:
            ligne = mot
        elif len(ligne) + 1 + len(mot) <= largeur:
            ligne += " " + mot
        else:
            lignes.append(ligne)
            ligne = mot
    if ligne:
        lignes.append(ligne)
    return lignes


# --- Affichage sur l'écran ----------------------------------------------

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


def afficher_message(epd, texte):
    """Écrit le texte le plus gros possible, sur plusieurs lignes si besoin."""
    marge = 10
    for scale in (6, 5, 4, 3, 2, 1):
        par_ligne = (epd.width - 2 * marge) // (8 * scale)
        lignes = couper(texte, par_ligne)
        interligne = 2 * scale
        hauteur = len(lignes) * (8 * scale + interligne) - interligne
        if hauteur <= epd.height - 2 * marge:
            break                               # cette taille tient à l'écran
    epd.fill(0)
    epd.rect(0, 0, epd.width, epd.height, 1)
    y = (epd.height - hauteur) // 2
    for ligne in lignes:
        texte_centre(epd, ligne, y, scale)
        y += 8 * scale + interligne
    epd.update()


def afficher_instructions(epd, adresse):
    epd.fill(0)
    epd.rect(0, 0, epd.width, epd.height, 1)
    texte_centre(epd, "Ecris-moi", 12, scale=3)
    epd.text("1. WiFi : " + NOM_RESEAU, 10, 52, 1)
    epd.text("2. Mot de passe : " + MOT_DE_PASSE, 10, 68, 1)
    epd.text("3. Safari : " + adresse, 10, 84, 1)
    epd.update()


# --- Page web ------------------------------------------------------------

def page_html(info):
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>Ecran e-paper</title>
<style>
body { font-family: -apple-system, sans-serif; max-width: 420px; margin: 0 auto;
       padding: 24px 16px; background: #f5f5f0; color: #222; }
h1 { font-size: 1.3rem; }
input[type=text] { width: 100%; font-size: 1.2rem; padding: 12px;
                   border: 2px solid #222; border-radius: 10px; box-sizing: border-box; }
button { width: 100%; margin-top: 14px; padding: 14px; font-size: 1.1rem;
         font-weight: 700; background: #222; color: #fff; border: 0; border-radius: 10px; }
p.info { margin-top: 18px; padding: 10px; background: #fff; border-radius: 10px; }
</style>
</head>
<body>
<h1>Ecris sur l'ecran</h1>
<form action="/" method="get">
<input type="text" name="t" maxlength="@MAX@" placeholder="Ton message" autofocus>
<button type="submit">Afficher</button>
</form>
<p class="info">@INFO@</p>
</body>
</html>""".replace("@MAX@", str(LONGUEUR_MAX)).replace("@INFO@", info)


def repondre(conn, info):
    corps = page_html(info)
    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
              "Connection: close\r\n\r\n")
    conn.send(corps)


# --- Programme principal -------------------------------------------------

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=NOM_RESEAU, password=MOT_DE_PASSE, authmode=network.AUTH_WPA_WPA2_PSK)
adresse = ap.ifconfig()[0]
print("Réseau WiFi :", NOM_RESEAU)
print("Adresse     :", adresse)

# On ne met PAS l'écran en deep_sleep entre deux affichages : il faudrait le
# réveiller avec un reset matériel.
epd = init_epd(rotation=ROTATION_90)
afficher_instructions(epd, adresse)

serveur = socket.socket()
serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serveur.bind(("0.0.0.0", 80))
serveur.listen(2)

dernier = None                                  # heure du dernier affichage (ms)
print("Serveur prêt. Ouvre http://" + adresse + " sur ton téléphone.")

while True:
    conn, _ = serveur.accept()
    conn.settimeout(3)
    try:
        requete = conn.recv(1024).decode()
        chemin = requete.split(" ")[1] if " " in requete else "/"
    except Exception:
        conn.close()
        continue

    nouveau_texte = None
    if chemin.startswith("/?t="):
        brut = chemin[4:].split("&")[0]
        texte = sans_accents(decoder(brut)).strip()[:LONGUEUR_MAX]
        if not texte:
            info = "Message vide ou illisible."
        elif dernier is not None and time.ticks_diff(time.ticks_ms(), dernier) < DELAI_MINI * 1000:
            info = "Trop vite ! L'ecran a besoin de quelques secondes de repos."
        else:
            nouveau_texte = texte
            info = "Envoye : " + texte + ". L'ecran se met a jour (2 secondes)."
    elif chemin == "/":
        info = "Pret. Ecris un message ci-dessus."
    else:
        conn.send("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
        conn.close()
        continue

    repondre(conn, info)                        # on répond AVANT de redessiner
    conn.close()

    if nouveau_texte:
        print("Message :", nouveau_texte)
        afficher_message(epd, nouveau_texte)
        dernier = time.ticks_ms()
