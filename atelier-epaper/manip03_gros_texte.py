# Atelier 02 — E-paper — Manip 03 : agrandir le texte
# Fablab Ardèche — MicroPython
#
# La police intégrée fait 8 pixels de haut, c'est petit. big_text() écrit le
# texte dans un mini-tampon, puis redessine chaque pixel sous forme d'un carré
# de « scale × scale » pixels.
#
# Attention : la police est en ASCII pur. Pas d'accents (é, è, à...).
#
# Matériel : carte LilyGo T5 V2.3 (écran e-paper déjà câblé)

from gdeh0213b73 import init_epd, ROTATION_90
import framebuf


def big_text(epd, s, x, y, scale=2, c=1):
    """Texte agrandi : scale=1 → 8 px de haut, scale=2 → 16, scale=3 → 24..."""
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
    """Comme big_text, mais calcule x pour centrer le texte."""
    largeur = len(s) * 8 * scale
    x = (epd.width - largeur) // 2
    big_text(epd, s, x, y, scale, c)


epd = init_epd(rotation=ROTATION_90)  # paysage : 250 de large, 128 de haut
epd.fill(0)

epd.text("8 px : texte normal", 4, 4, 1)
big_text(epd, "16 px", 4, 18, scale=2)
big_text(epd, "24 px", 4, 40, scale=3)
texte_centre(epd, "32 px", 76, scale=4)

epd.update()
epd.deep_sleep()
