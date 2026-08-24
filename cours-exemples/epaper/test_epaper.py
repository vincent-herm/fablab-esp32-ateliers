# test_epaper.py — LilyGo T5 V2.3 — Test e-paper avec tailles de texte
# -----------------------------------------------------------------------
# Bibliothèque : gdeh0213b73.py (copier sur l'ESP32)
#   fill(0) = blanc   fill(1) = noir
# -----------------------------------------------------------------------

from gdeh0213b73 import init_epd, ROTATION_0
import framebuf

def big_text(epd, s, x, y, scale=2, c=1):
    """Texte agrandi :  scale=1 → 8px   scale=2 → 16px   scale=3 → 24px"""
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

print("Init...")
epd = init_epd(rotation=ROTATION_0)   # 128 × 250 portrait

epd.fill(0)   # fond blanc

epd.text    ("8px  — texte normal",  4, 10, 1)   # scale 1 = 8px  (defaut)
big_text(epd, "16px scale 2",        4, 26, scale=2)   # 16px
big_text(epd, "24px",                4, 52, scale=3)   # 24px
big_text(epd, "32px",                4, 86, scale=4)   # 32px

epd.rect(2, 2, 124, 246, 1)   # cadre

print("Affichage... (~2s)")
epd.update()
epd.deep_sleep()
print("OK !")
