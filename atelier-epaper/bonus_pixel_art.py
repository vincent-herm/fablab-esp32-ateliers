# Atelier 02 — E-paper — Bonus : dessiner avec des caractères
# Fablab Ardèche — MicroPython
#
# Une image de 16 x 16 pixels est décrite par 16 chaînes de caractères :
# « # » = pixel noir, « . » = pixel blanc. La fonction dessiner() agrandit
# chaque pixel en carré de « echelle × echelle » pixels.
#
# Dessine ton propre motif en modifiant les # et les . ci-dessous.
#
# Matériel : carte LilyGo T5 V2.3 (écran e-paper déjà câblé)

from gdeh0213b73 import init_epd, ROTATION_90

SMILEY = [
    "......####......",
    "....########....",
    "..############..",
    ".##############.",
    ".###..####..###.",
    ".###..####..###.",
    ".##############.",
    "################",
    "################",
    "###.########.###",
    "####........####",
    ".##############.",
    "..############..",
    "....########....",
    "......####......",
    "................",
]

COEUR = [
    "................",
    "..####....####..",
    ".######..######.",
    "################",
    "################",
    "################",
    "################",
    ".##############.",
    "..############..",
    "...##########...",
    "....########....",
    ".....######.....",
    "......####......",
    ".......##.......",
    "................",
    "................",
]


def dessiner(epd, image, x0, y0, echelle, c=1):
    for y, ligne in enumerate(image):
        for x, pixel in enumerate(ligne):
            if pixel == "#":
                epd.fill_rect(x0 + x * echelle, y0 + y * echelle, echelle, echelle, c)


epd = init_epd(rotation=ROTATION_90)
epd.fill(0)

dessiner(epd, SMILEY, 20, 10, 6)      # 16 x 6 = 96 pixels de côté
dessiner(epd, COEUR, 134, 10, 6)
epd.text("Dessine le tien !", 65, 114, 1)

epd.update()
epd.deep_sleep()
