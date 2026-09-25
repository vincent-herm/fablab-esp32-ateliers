# Atelier 02 — E-paper — Manip 04 : lignes, rectangles, motifs
# Fablab Ardèche — MicroPython
#
# Les outils de dessin de MicroPython (module framebuf) :
#   rect(x, y, l, h, c)        rectangle vide
#   fill_rect(x, y, l, h, c)   rectangle plein
#   line(x1, y1, x2, y2, c)    ligne quelconque
#   hline / vline              lignes horizontales / verticales
#
# Origine (0, 0) = coin haut-gauche. En paysage : x de 0 à 249, y de 0 à 127.
#
# Matériel : carte LilyGo T5 V2.3 (écran e-paper déjà câblé)

from gdeh0213b73 import init_epd, ROTATION_90

epd = init_epd(rotation=ROTATION_90)
epd.fill(0)

# --- Un cadre à double trait ---
epd.rect(0, 0, epd.width, epd.height, 1)
epd.rect(3, 3, epd.width - 6, epd.height - 6, 1)

# --- Une cible : des rectangles emboîtés ---
for i in range(0, 40, 8):
    epd.rect(15 + i, 20 + i, 90 - 2 * i, 90 - 2 * i, 1)

# --- Un damier de 4 x 4 cases ---
for ligne in range(4):
    for col in range(4):
        if (ligne + col) % 2 == 0:
            epd.fill_rect(130 + col * 24, 20 + ligne * 24, 24, 24, 1)

# --- Deux diagonales ---
epd.line(130, 20, 226, 116, 1)
epd.line(130, 116, 226, 20, 1)

epd.update()
epd.deep_sleep()
