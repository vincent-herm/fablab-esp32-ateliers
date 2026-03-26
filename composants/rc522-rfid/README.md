# Lecteur RFID RC522 (Joy-it / MFRC522)

Lecteur de badges sans contact 13,56 MHz (Mifare), interface SPI.

---

## Câblage ESP32

**Le RC522 fonctionne en 3,3V. Ne JAMAIS le brancher en 5V.**

| Module RC522 | ESP32 | Notes |
|---|---|---|
| **3.3V** | **3.3V** | Alimentation 3,3V uniquement |
| **GND** | **GND** | |
| **SCK** | **D18** | Horloge SPI |
| **MOSI** | **D23** | Données ESP32 → RC522 |
| **MISO** | **D19** | Données RC522 → ESP32 |
| **SDA** | **D5** | Chip Select (CS) |
| **RST** | **D22** | Reset |
| **IRQ** | *(non connecté)* | Interruption (optionnel) |

7 fils + alimentation.

---

## Installation de la bibliothèque

La bibliothèque `mfrc522` s'installe une seule fois :

**Dans Thonny** : Outils → Gérer les paquets → chercher `mfrc522` → Installer

**Ou dans le Shell** :
```python
import mip
mip.install("mfrc522")
```

---

## Fichiers

| Fichier | Description |
|---|---|
| `test_rfid.py` | Test rapide : lit et affiche l'UID des badges |
| `exemple_controle_acces.py` | Contrôle d'accès complet (LEDs + buzzer) |
| `README.md` | Cette documentation |

---

## Utilisation rapide (Shell)

```python
from machine import Pin, SPI
from mfrc522 import MFRC522

spi  = SPI(1, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rfid = MFRC522(spi, gpioRst=22, gpioCs=5)

# Présenter un badge puis taper :
stat, tag = rfid.request(rfid.REQIDL)
stat, uid = rfid.anticoll()
print(':'.join(f'{b:02X}' for b in uid))
```

---

## Principe de fonctionnement

1. Le RC522 émet un champ radio à 13,56 MHz
2. Quand un badge (carte Mifare) entre dans le champ, il s'alimente par induction
3. Le badge renvoie son **UID** (identifiant unique, 4 octets) : ex. `DE:AD:BE:EF`
4. Le programme compare l'UID à une liste de badges autorisés
5. Décision : accès accordé ou refusé

Chaque badge a un UID unique gravé en usine — impossible à modifier.

---

## Source

Bibliothèque : [micropython-mfrc522](https://github.com/cefn/micropython-mfrc522) — installable via `mip`
