# Matrice LED MAX7219 (module 1088AS)

Afficheur 8×32 pixels (4 modules 1088AS en cascade), piloté par des circuits MAX7219 via SPI.

---

## Câblage ESP32

**ATTENTION : brancher sur le connecteur DIN (entrée), pas DOUT (sortie).**

| Module MAX7219 | ESP32 | Notes |
|---|---|---|
| **VCC** | **5V (VIN)** | Ne fonctionne PAS en 3.3V |
| **GND** | **GND** | |
| **DIN** | **D23** | GPIO23 = MOSI (données SPI) |
| **CLK** | **D18** | GPIO18 = SCK (horloge SPI) |
| **CS** | **D5** | GPIO5 = Chip Select |

Tous les pins ESP32 sont du côté bas de la carte (de 3V3 à D23).

---

## Fichiers

| Fichier | Description |
|---|---|
| `max7219.py` | Bibliothèque MicroPython (mcauser, licence MIT) — à copier sur l'ESP32 |
| `test_matrice.py` | Test rapide : texte, remplissage, défilement |
| `exemple_texte.py` | Afficher du texte fixe, régler la luminosité |
| `exemple_defilement.py` | Texte défilant (bandeau d'information) |
| `exemple_animations.py` | 5 animations : pixels, balayage, rectangle, compteur, barre de progression |

---

## Installation

1. Copier `max7219.py` sur l'ESP32 via Thonny (clic droit → Upload to /)
2. Ouvrir un des exemples dans Thonny
3. Lancer avec F5

---

## Utilisation rapide (Shell Thonny)

```python
from machine import Pin, SPI
import max7219

spi = SPI(2, baudrate=10000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)
ecran = max7219.Matrix8x8(spi, cs, 4)
ecran.brightness(5)

ecran.fill(0)
ecran.text("HELLO", 0, 0, 1)
ecran.show()
```

---

## Méthodes disponibles

| Méthode | Description |
|---|---|
| `fill(0)` / `fill(1)` | Tout éteindre / tout allumer |
| `pixel(x, y, 1)` | Allumer un pixel |
| `text("ABC", x, y, 1)` | Écrire du texte (~8px par caractère) |
| `hline(x, y, w, 1)` | Ligne horizontale |
| `vline(x, y, h, 1)` | Ligne verticale |
| `line(x1, y1, x2, y2, 1)` | Ligne quelconque |
| `rect(x, y, w, h, 1)` | Rectangle vide |
| `fill_rect(x, y, w, h, 1)` | Rectangle plein |
| `scroll(dx, dy)` | Décaler le contenu |
| `brightness(0..15)` | Luminosité (0 = min, 15 = max) |
| `show()` | **Afficher** (obligatoire après chaque modification) |

---

## Coordonnées

- Origine (0, 0) = coin haut-gauche
- X : 0 à 31 (horizontal, 32 colonnes)
- Y : 0 à 7 (vertical, 8 lignes)
- Couleur : 1 = allumé, 0 = éteint

---

## Source

Bibliothèque : [mcauser/micropython-max7219](https://github.com/mcauser/micropython-max7219) — Licence MIT
