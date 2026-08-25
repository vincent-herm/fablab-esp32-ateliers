# payzac_fablab.py — LilyGo T5 V2.3 — Affiche "Payzac et son FabLab"
# -----------------------------------------------------------------------
# Bibliothèque : gdeh0213b73.py (à copier sur l'ESP32)
#   fill(0) = blanc   fill(1) = noir
#
# Écran 2.13" : 128 × 250 en portrait, 250 × 128 en paysage.
# Ici on travaille en PAYSAGE (ROTATION_90) : plus large, donc plus
# confortable pour du texte.
#
# ATTENTION : la police intégrée de framebuf est en ASCII pur.
# Les accents (é, è, à...) ne s'affichent pas correctement.
# D'où "Ardeche" sans accent dans la ligne du bas.
# -----------------------------------------------------------------------

from gdeh0213b73 import init_epd, ROTATION_90
import framebuf


def big_text(epd, s, x, y, scale=2, c=1):
    """Texte agrandi : scale=1 → 8px, scale=2 → 16px, scale=3 → 24px..."""
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


def texte_centre(epd, s, y, scale=2, c=1):
    """Comme big_text, mais calcule x tout seul pour centrer le texte."""
    largeur = len(s) * 8 * scale          # largeur totale en pixels
    x = (epd.width - largeur) // 2        # marge égale à gauche et à droite
    big_text(epd, s, x, y, scale, c)
    return x


print("Initialisation de l'ecran...")
epd = init_epd(rotation=ROTATION_90)      # 250 × 128 paysage

epd.fill(0)                               # fond blanc

# --- Cadre extérieur (double trait) ---
epd.rect(0, 0, epd.width,     epd.height,     1)
epd.rect(3, 3, epd.width - 6, epd.height - 6, 1)

# --- Le texte, centré ---
texte_centre(epd, "PAYZAC",  16, scale=4)   # 32 px de haut
texte_centre(epd, "et son",  54, scale=2)   # 16 px
texte_centre(epd, "FabLab",  76, scale=4)   # 32 px

# --- Filets décoratifs de part et d'autre de "et son" ---
epd.hline(28,  61, 44, 1)
epd.hline(178, 61, 44, 1)

# --- Ligne du bas ---
texte_centre(epd, "Ardeche . MicroPython . ESP32", 114, scale=1)

print("Affichage en cours... (~2 s)")
epd.update()          # rafraîchissement de la dalle
epd.deep_sleep()      # l'image RESTE affichée, même hors tension
print("OK ! L'image reste affichee sans alimentation.")

# -----------------------------------------------------------------------
# EXPÉRIENCES À TESTER :
#   - Remplace "PAYZAC" par ton prénom : texte_centre garde le centrage
#   - Passe scale=4 à scale=3 → texte plus petit, plus de place
#   - Enlève epd.deep_sleep() : l'image reste affichée quand même,
#     mais la carte consomme beaucoup plus
#   - Supprime le second epd.rect() → cadre simple au lieu de double
#   - Inverse la vidéo : epd.fill(1) puis passe c=0 dans chaque appel
#     → texte blanc sur fond noir
#
# À RETENIR — pourquoi un écran e-paper :
#   L'image est formée par de vraies micro-billes noires et blanches
#   déplacées par un champ électrique. Une fois en place, elles ne
#   bougent plus : l'affichage ne consomme RIEN pour être maintenu.
#   D'où les liseuses qui tiennent des semaines sur une charge.
#   En contrepartie, le rafraîchissement prend environ 2 secondes.
# -----------------------------------------------------------------------
