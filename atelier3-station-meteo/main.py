# Atelier 03 — Station météo (DS18B20 + OLED SSD1306)
# Fablab Ardèche — MicroPython
#
# Mesure la température avec un capteur DS18B20 (1-Wire)
# et affiche les données sur un écran OLED SSD1306.
#
# Matériel : ESP32, DS18B20, résistance 4.7kΩ, OLED SSD1306 128x64
# Connexions :
#   DS18B20 DATA → GPIO27  (+ résistance 4.7kΩ vers 3.3V)
#   OLED SDA     → GPIO21
#   OLED SCL     → GPIO22

from machine import Pin, I2C
import onewire, ds18x20
import ssd1306
import time, math

# --- Initialisation DS18B20 ---
ow  = onewire.OneWire(Pin(27))
ds  = ds18x20.DS18X20(ow)
capteurs = ds.scan()

if not capteurs:
    print("Aucun capteur DS18B20 trouvé !")
    print("Vérifie le câblage et la résistance 4.7kΩ")
else:
    print(f"{len(capteurs)} capteur(s) trouvé(s)")

# --- Initialisation OLED ---
i2c  = I2C(0, scl=Pin(22), sda=Pin(21), freq=400_000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# --- Historique pour le graphique ---
HIST_MAX = 64
historique = []

def lire_temperature():
    if not capteurs:
        return None
    ds.convert_temp()
    time.sleep_ms(750)
    return ds.read_temp(capteurs[0])

def afficher(temp, mini, maxi):
    oled.fill(0)

    if temp is None:
        oled.text("Capteur absent!", 0, 24)
        oled.show()
        return

    # Titre
    oled.text("Station Meteo", 0, 0)
    oled.hline(0, 10, 128, 1)

    # Température principale
    t_str = f"{temp:.1f}C"
    oled.text(t_str, 0, 16)

    # Mini / Maxi
    oled.text(f"min:{mini:.0f} max:{maxi:.0f}", 0, 30)

    # Graphique de l'historique
    if len(historique) >= 2:
        plage = maxi - mini if maxi != mini else 1
        for x, val in enumerate(historique[-64:]):
            y = int(63 - ((val - mini) / plage) * 18)
            y = max(44, min(63, y))
            oled.pixel(x, y, 1)

    oled.hline(0, 44, 128, 1)
    oled.show()

# --- Boucle principale ---
print("Station météo démarrée")
mini_t = 99.0
maxi_t = -99.0

while True:
    temp = lire_temperature()

    if temp is not None:
        if temp < mini_t:
            mini_t = temp
        if temp > maxi_t:
            maxi_t = temp
        historique.append(temp)
        if len(historique) > HIST_MAX:
            historique.pop(0)
        print(f"Température : {temp:.2f} °C  (min {mini_t:.1f} / max {maxi_t:.1f})")

    afficher(temp, mini_t, maxi_t)
    time.sleep(2)
