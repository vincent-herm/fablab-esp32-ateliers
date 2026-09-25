# Atelier 02 — E-paper (2 h)

Carte **LilyGo T5 V2.3** : ESP32 + écran e-paper 2,13" (250 × 128 pixels) déjà câblé. Rien à brancher, à part le câble USB.

Le pilote de l'écran, `gdeh0213b73.py`, se trouve dans `../cours-exemples/epaper/`. Il faut le téléverser sur la carte (Thonny : Affichage → Fichiers, clic droit → Téléverser vers /).

## Déroulé

| Durée | Étape | Fichier |
|---|---|---|
| 10 min | Présentation de l'e-paper | |
| 15 min | Installer la bibliothèque | `manip01_verifier_installation.py` |
| 10 min | Premier affichage | `manip02_premier_affichage.py` |
| 15 min | Agrandir le texte | `manip03_gros_texte.py` |
| 10 min | Formes et motifs | `manip04_formes.py` |
| 20 min | Badge nominatif | `manip05_badge.py` |
| 15 min | Pixel art | `manip06_pixel_art.py` |
| 15 min | Compteur avec le bouton BOOT | `manip07_compteur_bouton.py` |
| 10 min | Questions, bonus (`../cours-exemples/epaper/payzac_fablab.py`) | |

Page du site : https://fablab.opentek.fr/ateliers/epaper/

## À savoir

- Police intégrée en ASCII pur : pas d'accents.
- Rafraîchissement d'environ 2 s ; les appuis de bouton pendant ce temps sont perdus (manip 07).
- Manip 07 : le bouton BOOT est supposé sur GPIO0. À vérifier sur la carte (constante `BOUTON`).
