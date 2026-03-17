# Atelier 07 — Minuterie et séquenceur (machine à états)
# Fablab Ardèche — MicroPython
#
# Un système de minuterie avec plusieurs modes :
# - Minuterie simple (durée réglable avec les boutons)
# - Séquenceur de LEDs (pattern lumineux programmable)
# - Feux de circulation (simulation)
#
# Ce projet illustre la programmation non-bloquante avec ticks_ms()
# et le concept de machine à états.
#
# Matériel : ESP32, 3 LEDs (rouge/orange/verte), 2 boutons, buzzer
# Connexions :
#   LED rouge   → GPIO23
#   LED orange  → GPIO19
#   LED verte   → GPIO18
#   Bouton +    → GPIO25 (PULL_UP)
#   Bouton -    → GPIO26 (PULL_UP)
#   Bouton MODE → GPIO0  (PULL_UP)
#   Buzzer      → GPIO5

from machine import Pin, PWM
import time

# --- Initialisation ---
led_r = Pin(23, Pin.OUT)
led_o = Pin(19, Pin.OUT)
led_v = Pin(18, Pin.OUT)
leds  = [led_r, led_o, led_v]

bp_plus  = Pin(25, Pin.IN, Pin.PULL_UP)
bp_moins = Pin(26, Pin.IN, Pin.PULL_UP)
bp_mode  = Pin(0,  Pin.IN, Pin.PULL_UP)

buz = PWM(Pin(5))
buz.duty(0)

def eteindre_tout():
    for led in leds:
        led.off()

def bip(freq=1000, duree=80):
    buz.freq(freq)
    buz.duty(200)
    time.sleep_ms(duree)
    buz.duty(0)

# ============================================================
# MODE 1 — Minuterie simple
# ============================================================
def mode_minuterie():
    duree_s   = 10
    t_appui   = time.ticks_ms()
    actif     = False
    t_depart  = 0

    print(f"\n=== MINUTERIE ===")
    print("+ / - pour régler la durée, MODE pour démarrer")

    t_btn_p = t_btn_m = time.ticks_ms()

    while True:
        now = time.ticks_ms()

        # Bouton + : augmenter la durée
        if bp_plus.value() == 0 and time.ticks_diff(now, t_btn_p) > 250:
            t_btn_p = now
            duree_s = min(duree_s + 5, 300)
            print(f"Durée : {duree_s} s")
            bip(1200, 50)

        # Bouton - : diminuer la durée
        if bp_moins.value() == 0 and time.ticks_diff(now, t_btn_m) > 250:
            t_btn_m = now
            duree_s = max(duree_s - 5, 5)
            print(f"Durée : {duree_s} s")
            bip(800, 50)

        # Bouton MODE : démarrer/arrêter ou changer de mode
        if bp_mode.value() == 0 and time.ticks_diff(now, t_appui) > 400:
            t_appui = now
            if not actif:
                actif    = True
                t_depart = now
                print(f"Démarrage — {duree_s}s")
                bip(1500, 100)
            else:
                actif = False
                eteindre_tout()
                print("Arrêté")
                bip(600, 200)
            while bp_mode.value() == 0:
                time.sleep_ms(20)
            # Retour au sélecteur de mode
            if not actif:
                return

        # Logique minuterie active
        if actif:
            ecoule = time.ticks_diff(now, t_depart) // 1000
            restant = duree_s - ecoule

            if restant <= 0:
                # Temps écoulé !
                eteindre_tout()
                for _ in range(5):
                    led_v.toggle()
                    bip(2000, 150)
                    time.sleep_ms(150)
                eteindre_tout()
                actif = False
                print("Terminé !")
                return
            else:
                # Clignoter la LED verte (1 Hz)
                led_v.value((now // 500) % 2)
                # Dernières 5 secondes : accélérer
                if restant <= 5:
                    led_r.value((now // 200) % 2)
                print(f"\rRestant : {restant:3d}s  ", end="")

        time.sleep_ms(50)

# ============================================================
# MODE 2 — Séquenceur de LEDs
# ============================================================
def mode_sequenceur():
    # Séquences : liste de (rouge, orange, vert, durée_ms)
    sequences = [
        (1, 0, 0, 500),
        (0, 1, 0, 500),
        (0, 0, 1, 500),
        (1, 1, 0, 300),
        (0, 1, 1, 300),
        (1, 0, 1, 300),
        (1, 1, 1, 200),
        (0, 0, 0, 200),
    ]

    etat = 0
    t0   = time.ticks_ms()
    t_mode = time.ticks_ms()

    print("\n=== SÉQUENCEUR ===")
    print("MODE pour quitter")

    while True:
        now = time.ticks_ms()

        # Appliquer l'état courant
        r, o, v, duree = sequences[etat]
        led_r.value(r)
        led_o.value(o)
        led_v.value(v)

        if time.ticks_diff(now, t0) >= duree:
            etat = (etat + 1) % len(sequences)
            t0   = now

        if bp_mode.value() == 0 and time.ticks_diff(now, t_mode) > 400:
            eteindre_tout()
            while bp_mode.value() == 0:
                time.sleep_ms(20)
            return

        time.sleep_ms(10)

# ============================================================
# MODE 3 — Feux de circulation
# ============================================================
def mode_feux():
    # États : (rouge, orange, vert, durée_ms, description)
    feux = [
        (1, 0, 0, 4000, "ROUGE — stop"),
        (1, 1, 0, 1000, "ROUGE+ORANGE — prêt"),
        (0, 0, 1, 4000, "VERT — passez"),
        (0, 1, 0, 1500, "ORANGE — attention"),
    ]

    etat  = 0
    t0    = time.ticks_ms()
    t_mode = time.ticks_ms()

    print("\n=== FEUX DE CIRCULATION ===")
    r, o, v, duree, desc = feux[etat]
    print(f"  {desc}")

    while True:
        now = time.ticks_ms()
        r, o, v, duree, desc = feux[etat]
        led_r.value(r)
        led_o.value(o)
        led_v.value(v)

        if time.ticks_diff(now, t0) >= duree:
            etat = (etat + 1) % len(feux)
            t0   = now
            print(f"  {feux[etat][4]}")

        if bp_mode.value() == 0 and time.ticks_diff(now, t_mode) > 400:
            eteindre_tout()
            while bp_mode.value() == 0:
                time.sleep_ms(20)
            return

        time.sleep_ms(10)

# ============================================================
# Sélecteur de mode
# ============================================================
MODES_DISPO = [
    ("Minuterie",    mode_minuterie),
    ("Séquenceur",   mode_sequenceur),
    ("Feux",         mode_feux),
]
mode_idx = 0

print("Minuterie & Séquenceur — Fablab Ardèche")
print("Appuie sur MODE (BOOT) pour changer de programme")

t_mode = time.ticks_ms()

while True:
    now = time.ticks_ms()

    if bp_mode.value() == 0 and time.ticks_diff(now, t_mode) > 400:
        t_mode = now
        nom, fn = MODES_DISPO[mode_idx]
        bip(1000, 100)
        fn()
        mode_idx = (mode_idx + 1) % len(MODES_DISPO)
        print(f"\nProchain mode : {MODES_DISPO[mode_idx][0]}")
        while bp_mode.value() == 0:
            time.sleep_ms(20)

    # Clignote la LED correspondant au mode sélectionné
    eteindre_tout()
    leds[mode_idx].value((now // 600) % 2)
    time.sleep_ms(20)
