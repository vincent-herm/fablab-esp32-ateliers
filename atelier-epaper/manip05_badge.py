# Atelier 02 — E-paper — Manip 05 : ton badge nominatif
# Fablab Ardèche — MicroPython
#
# Ton prénom s'affiche en aussi gros que possible, centré. Comme l'écran
# e-paper garde l'image sans courant, tu peux débrancher la carte et
# la garder comme badge, magnet ou porte-clés.
#
# Change PRENOM, puis lance le programme (F5).
#
# Matériel : carte LilyGo T5 V2.3 (écran e-paper déjà câblé)

from gdeh0213b73 import init_epd, ROTATION_90
import framebuf

PRENOM = "Camille"                    # ASCII seulement : pas d'accents !
LIGNE2 = "Fablab Payzac"


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


def echelle_max(epd, s, maxi=6):
    """Plus grand agrandissement qui tient dans la largeur de l'écran."""
    scale = maxi
    while scale > 1 and len(s) * 8 * scale > epd.width - 16:
        scale -= 1
    return scale


epd = init_epd(rotation=ROTATION_90)
epd.fill(0)

epd.rect(0, 0, epd.width, epd.height, 1)
epd.rect(3, 3, epd.width - 6, epd.height - 6, 1)

echelle = echelle_max(epd, PRENOM)
haut = 8 * echelle                            # hauteur du prénom en pixels
y_prenom = 18 + (60 - haut) // 2
texte_centre(epd, PRENOM, y_prenom, scale=echelle)

epd.hline(20, 88, epd.width - 40, 1)
texte_centre(epd, LIGNE2, 98, scale=2)

epd.update()
epd.deep_sleep()
print("Badge affiché. Tu peux débrancher la carte : l'image reste.")
