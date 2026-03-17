# Atelier 06 — Mesure de distance (HC-SR04 + OLED)
# Fablab Ardèche — MicroPython
#
# Le capteur ultrason HC-SR04 mesure la distance d'un obstacle.
# Le résultat s'affiche sur l'écran OLED avec une barre de progression.
# Une LED et un buzzer alertent quand on est trop proche.
#
# Matériel : ESP32, HC-SR04, OLED SSD1306, LED, buzzer
# Connexions :
#   HC-SR04 TRIG → GPIO12
#   HC-SR04 ECHO → GPIO14  (attention : l'ECHO sort en 5V, diviser par 2 avec résistances)
#   OLED SDA     → GPIO21
#   OLED SCL     → GPIO22
#   LED alerte   → GPIO2
#   Buzzer       → GPIO5

from machine import Pin, PWM, I2C, time_pulse_us
import ssd1306
import time

# --- Configuration ---
DIST_ALERTE = 20   # cm — en dessous : alerte
DIST_MAX    = 200  # cm — distance maximale affichée

# --- Initialisation ---
trig  = Pin(12, Pin.OUT)
echo  = Pin(14, Pin.IN)
led   = Pin(2, Pin.OUT)
buz   = PWM(Pin(5))
buz.duty(0)

i2c  = I2C(0, scl=Pin(22), sda=Pin(21), freq=400_000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

def mesurer_cm():
    """Déclenche une mesure et retourne la distance en cm."""
    # Impulsion TRIG de 10 µs
    trig.off()
    time.sleep_us(2)
    trig.on()
    time.sleep_us(10)
    trig.off()

    # Mesurer la durée de l'impulsion ECHO (timeout = 30 ms)
    duree = time_pulse_us(echo, 1, 30000)

    if duree < 0:
        return None   # timeout = pas d'obstacle détecté

    # Vitesse du son : 343 m/s → 0.0343 cm/µs → diviser par 2 (aller-retour)
    return duree * 0.0343 / 2

def barre(valeur, maxi, largeur=100):
    """Calcule la largeur d'une barre de progression en pixels."""
    return min(largeur, int(valeur / maxi * largeur))

def afficher(dist):
    oled.fill(0)
    oled.text("Distance", 0, 0)
    oled.hline(0, 10, 128, 1)

    if dist is None:
        oled.text("Hors portee", 0, 24)
        oled.text("> 2 m", 0, 38)
    else:
        # Valeur numérique
        if dist < 100:
            oled.text(f"{dist:.1f} cm", 0, 16)
        else:
            oled.text(f"{dist/100:.2f} m", 0, 16)

        # Barre de progression
        l = barre(min(dist, DIST_MAX), DIST_MAX, 120)
        oled.fill_rect(4, 30, l, 10, 1)
        oled.rect(4, 30, 120, 10, 1)

        # Indicateur d'alerte
        if dist < DIST_ALERTE:
            oled.text("!! TROP PROCHE !!", 0, 50)

    oled.show()

# --- Boucle principale ---
print("Capteur ultrason démarré")
print(f"Alerte sous {DIST_ALERTE} cm")

while True:
    dist = mesurer_cm()

    if dist is not None:
        print(f"Distance : {dist:.1f} cm")

        # Alerte sonore + LED
        if dist < DIST_ALERTE:
            led.on()
            freq_buz = int(2000 - dist * 50)   # plus proche = plus aigu
            buz.freq(max(200, freq_buz))
            buz.duty(200)
        else:
            led.off()
            buz.duty(0)
    else:
        print("Hors portée")
        led.off()
        buz.duty(0)

    afficher(dist)
    time.sleep_ms(100)
