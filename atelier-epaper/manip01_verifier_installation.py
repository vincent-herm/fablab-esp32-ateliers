# Atelier 02 — E-paper — Manip 01 : vérifier que la bibliothèque est installée
# Fablab Ardèche — MicroPython
#
# Aucun affichage ici : on vérifie seulement que le fichier gdeh0213b73.py
# est bien sur l'ESP32 et que Python arrive à le lire.
#
# Matériel : carte LilyGo T5 V2.3 (l'écran e-paper est déjà câblé dessus)
# Rien à brancher, à part le câble USB.

import os

print("Fichiers présents sur l'ESP32 :")
print(os.listdir())

try:
    import gdeh0213b73
    print("OK : la bibliothèque est installée.")
    print("Fonctions disponibles :", [n for n in dir(gdeh0213b73) if not n.startswith("_")][:8])
except ImportError:
    print("MANQUE : gdeh0213b73.py n'est pas sur l'ESP32.")
    print("Dans Thonny : Affichage > Fichiers, clic droit sur le fichier > Téléverser vers /")
