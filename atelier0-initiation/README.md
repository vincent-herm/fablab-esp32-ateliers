# Atelier 0 — Initiation à l'ESP32 et MicroPython

**Fablab Polinno — Beaume Drobie — 9 avril 2026**

Durée : 3 heures · Niveau : Grand débutant · 6 à 10 participants

---

## Matériel nécessaire

- 1 carte ESP32 par participant
- 1 câble USB (micro-USB ou USB-C selon la carte)
- 1 ordinateur par participant avec **Thonny** installé
- 1 smartphone par participant (pour la manip finale)

**Rien à brancher sur breadboard — toutes les manips utilisent la LED et le bouton intégrés à la carte.**

---

## Avant l'atelier

1. Installer **Thonny** sur chaque ordinateur : https://thonny.org
2. Flasher **MicroPython** sur chaque ESP32 via Thonny (Tools → Manage plug-ins → MicroPython ESP32)
3. Vérifier que chaque carte est reconnue dans Thonny (barre de statut en bas à droite)

---

## Les 10 manipulations

| # | Fichier | Durée | Ce qu'on apprend |
|---|---|---|---|
| 01 | `manip01_repl.py` | 10 min | REPL interactif, Python en direct |
| 02 | `manip02_led_on_off.py` | 10 min | GPIO sortie, allumer/éteindre |
| 03 | `manip03_led_blink.py` | 10 min | Boucle infinie, `while True` |
| 04 | `manip04_led_pwm.py` | 15 min | PWM, luminosité variable |
| 05 | `manip05_bouton_boot.py` | 10 min | GPIO entrée, lecture d'un bouton |
| 06 | `manip06_led_bouton.py` | 10 min | Capteur → actionneur |
| 07 | `manip07_temperature_interne.py` | 10 min | Capteur interne, f-strings |
| 08 | `manip08_scan_wifi.py` | 10 min | Module réseau, scan WiFi |
| 09 | `manip09_point_acces_wifi.py` | 10 min | Créer un réseau WiFi |
| 10 | `manip10_serveur_web_led.py` | 25 min | Serveur HTTP, contrôle depuis le téléphone |

**Total : ~2h — les 60 minutes restantes couvrent l'installation, les questions et les imprévus.**

---

## Déroulé suggéré

**0:00 — Accueil et présentation** (15 min)
- Qu'est-ce qu'un microcontrôleur ? Où en trouve-t-on ?
- Présentation de l'ESP32 et de MicroPython
- Branchement des cartes, lancement de Thonny

**0:15 — Manips 01 à 04** (40 min)
- REPL, LED, blink, PWM
- Toutes les découvertes se font dans Thonny

**0:55 — Manips 05 et 06** (20 min)
- Bouton, automatisme entrée/sortie
- Discussion : c'est ça, l'électronique embarquée

**1:15 — Pause** (10 min)

**1:25 — Manips 07 et 08** (20 min)
- Température interne, scan WiFi
- Montrer que l'ESP32 "voit" le monde

**1:45 — Manip 09** (10 min)
- Chacun crée son réseau WiFi
- Les smartphones détectent les réseaux → moment collectif

**1:55 — Manip 10** (25 min)
- Serveur web : connecter le téléphone, contrôler la LED
- Grand final → photos, partage

**2:20 — Questions et suite** (40 min)
- Que peut-on faire d'autre avec l'ESP32 ?
- Présentation des prochains ateliers
- La carte est à vous — que voulez-vous en faire ?

---

## Notes pour l'animateur

- La manip 01 se fait dans le **Shell** de Thonny, pas comme un fichier à lancer
- Pour les manips 02 à 09 : **Fichier → Ouvrir → MicroPython device** puis exécuter avec F5
- Pour arrêter un programme en cours : **Ctrl+C**
- Si l'ESP32 est bloqué : **Ctrl+D** (soft reset) ou bouton RST sur la carte
- La LED intégrée est sur **GPIO 2** sur la quasi-totalité des cartes ESP32
- Le bouton BOOT est sur **GPIO 0** — il est déjà câblé avec une résistance pull-up
