# epaper_demo.py — LilyGo T5 V2.3 — Démo e-paper 2.13"
# -----------------------------------------------------------------------
# Bibliothèque : gdeh0213b73.py (copier sur l'ESP32)
# Résolution   : 128 × 250 pixels (portrait)
#
# Convention couleurs :
#   fill(0)          = fond blanc
#   fill(1)          = fond noir
#   text("...", c=1) = texte noir
#   text("...", c=0) = texte blanc (sur fond noir)
# -----------------------------------------------------------------------

from gdeh0213b73 import init_epd, ROTATION_0
import framebuf

def big_text(epd, s, x, y, scale=2, c=1):
    """Affiche du texte agrandi par scale (2=16px, 3=24px de haut)"""
    w   = len(s) * 8
    bpr = (w + 7) // 8
    buf = bytearray(bpr * 8)
    fb  = framebuf.FrameBuffer(buf, w, 8, framebuf.MONO_HLSB)
    fb.fill(0)
    fb.text(s, 0, 0, 1)
    for ty in range(8):
        for tx in range(w):
            if fb.pixel(tx, ty):
                epd.fill_rect(x + tx * scale, y + ty * scale, scale, scale, c)

# -----------------------------------------------------------------------
# Init écran en portrait 128 × 250
# -----------------------------------------------------------------------
print("Init e-paper...")
epd = init_epd(rotation=ROTATION_0)
W, H = epd.width, epd.height   # 128, 250

epd.fill(0)   # fond blanc

# -----------------------------------------------------------------------
# HEADER — bande noire avec titre blanc
# -----------------------------------------------------------------------
epd.fill_rect(0, 0, W, 52, 1)
big_text(epd, "FABLAB", 10, 5,  scale=3, c=0)   # 24px blanc
big_text(epd, "ARDECHE", 4, 32, scale=2, c=0)   # 16px blanc

# Double trait de séparation
epd.line(0, 54, W, 54, 1)
epd.line(0, 56, W, 56, 1)

# -----------------------------------------------------------------------
# INFOS
# -----------------------------------------------------------------------
epd.text("MicroPython + ESP32", 4, 65,  1)
epd.text("e-paper 2.13 pouces",  4, 77,  1)
epd.text("Ateliers debutants",   4, 93,  1)
epd.text("Payzac, Ardeche",      4, 105, 1)
epd.text("flowzen.fr/vincent",   4, 117, 1)

# Double trait de séparation
epd.line(0, 130, W, 130, 1)
epd.line(0, 132, W, 132, 1)

# -----------------------------------------------------------------------
# DÉCO — Damier (5 lignes × 8 colonnes de carrés 13px)
# -----------------------------------------------------------------------
for row in range(5):
    for col in range(8):
        x = 4 + col * 15
        y = 140 + row * 15
        if (row + col) % 2 == 0:
            epd.fill_rect(x, y, 13, 13, 1)
        else:
            epd.rect(x, y, 13, 13, 1)

# -----------------------------------------------------------------------
# DÉCO — Cible (carrés concentriques alternés)
# -----------------------------------------------------------------------
cx, cy = 64, 228
for i in range(6):
    s = 40 - i * 7
    if s > 1:
        ox, oy = cx - s // 2, cy - s // 2
        if i % 2 == 0:
            epd.rect(ox, oy, s, s, 1)
        else:
            epd.fill_rect(ox, oy, s, s, 1)
            epd.fill_rect(ox + 1, oy + 1, s - 2, s - 2, 0)

# -----------------------------------------------------------------------
# BORDURE GÉNÉRALE (double cadre)
# -----------------------------------------------------------------------
epd.rect(0, 0, W, H, 1)
epd.rect(2, 2, W - 4, H - 4, 1)

# -----------------------------------------------------------------------
# Envoi vers l'écran (~2 secondes)
# -----------------------------------------------------------------------
print("Affichage... (patience ~2s)")
epd.update()
epd.deep_sleep()
print("Done — e-paper en veille profonde")
