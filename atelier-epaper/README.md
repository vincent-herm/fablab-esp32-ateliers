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
| 15 min | Compteur avec le bouton (GPIO39) | `manip06_compteur_bouton.py` |
| 20 min | Écrire sur l'écran depuis un téléphone (serveur web) | `manip07_message_iphone.py` |
| 5 min | Questions. Bonus : `bonus_pixel_art.py`, `../cours-exemples/epaper/payzac_fablab.py` | |

Page du site : https://fablab.opentek.fr/ateliers/epaper/

## À savoir

- Police intégrée en ASCII pur : pas d'accents.
- Rafraîchissement d'environ 2 s ; les appuis de bouton pendant ce temps sont perdus (manip 06).
- Manip 06 : le bouton de la carte est sur GPIO39, entrée seule sans résistance de rappel interne. Le programme mesure l'état de repos au démarrage, donc le sens du bouton n'a pas d'importance.
- Manip 07 : chaque carte doit avoir son propre `NOM_RESEAU` (plusieurs cartes dans la salle). Mot de passe du réseau : `fablab2026`, adresse `192.168.4.1`. Délai minimal de 10 s entre deux affichages.
