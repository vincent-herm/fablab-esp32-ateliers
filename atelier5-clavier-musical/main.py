# Atelier 05 — Clavier musical (buzzer + boutons)
# Fablab Ardèche — MicroPython
#
# 4 boutons jouent des notes de musique sur un buzzer.
# Mode libre : chaque bouton = une note.
# Mode gamme : joue automatiquement une gamme complète.
#
# Matériel : ESP32, buzzer passif, 4 boutons poussoirs
# Connexions :
#   Buzzer → GPIO5  (PWM)
#   BP_1   → GPIO25 (PULL_UP) → Do
#   BP_2   → GPIO26 (PULL_UP) → Mi
#   BP_3   → GPIO27 (PULL_UP) → Sol
#   BP_4   → GPIO14 (PULL_UP) → Do (octave sup.)
#   BP_MODE→ GPIO0  (PULL_UP) → changer de mode

from machine import Pin, PWM
import time

# --- Notes (fréquences en Hz) ---
NOTES = {
    'Do3':  262, 'Re3':  294, 'Mi3':  330, 'Fa3':  349,
    'Sol3': 392, 'La3':  440, 'Si3':  494,
    'Do4':  523, 'Re4':  587, 'Mi4':  659, 'Fa4':  698,
    'Sol4': 784, 'La4':  880, 'Si4':  988,
    'Do5': 1047,
}

# Mélodies prédéfinies : liste de (note, durée_ms)
GAMME_DO = [
    ('Do3', 300), ('Re3', 300), ('Mi3', 300), ('Fa3', 300),
    ('Sol3', 300), ('La3', 300), ('Si3', 300), ('Do4', 600),
]

FRERE_JACQUES = [
    ('Do3',300),('Re3',300),('Mi3',300),('Do3',300),
    ('Do3',300),('Re3',300),('Mi3',300),('Do3',300),
    ('Mi3',300),('Fa3',300),('Sol3',600),
    ('Mi3',300),('Fa3',300),('Sol3',600),
    ('Sol3',150),('La3',150),('Sol3',150),('Fa3',150),('Mi3',300),('Do3',300),
    ('Sol3',150),('La3',150),('Sol3',150),('Fa3',150),('Mi3',300),('Do3',300),
    ('Do3',300),('Sol3',300-1),('Do3',600),  # -1 pour éviter 0
    ('Do3',300),('Sol3',300-1),('Do3',600),
]

AU_CLAIR_DE_LA_LUNE = [
    ('Do3',400),('Do3',400),('Do3',400),('Re3',400),
    ('Mi3',800),('Re3',800),
    ('Do3',400),('Mi3',400),('Re3',400),('Re3',400),
    ('Do3',1200),
]

# --- Initialisation ---
buzzer = PWM(Pin(5))
buzzer.duty(0)

bp1   = Pin(25, Pin.IN, Pin.PULL_UP)   # Do
bp2   = Pin(26, Pin.IN, Pin.PULL_UP)   # Mi
bp3   = Pin(27, Pin.IN, Pin.PULL_UP)   # Sol
bp4   = Pin(14, Pin.IN, Pin.PULL_UP)   # Do octave
bp_m  = Pin(0,  Pin.IN, Pin.PULL_UP)   # Mode

boutons_notes = [
    (bp1, 'Do3'),
    (bp2, 'Mi3'),
    (bp3, 'Sol3'),
    (bp4, 'Do4'),
]

MELODIES = [
    ("Gamme Do majeur",    GAMME_DO),
    ("Frère Jacques",      FRERE_JACQUES),
    ("Au clair de la lune",AU_CLAIR_DE_LA_LUNE),
]
mel_idx = 0

def jouer_note(freq, duree_ms=200):
    if freq == 0:
        buzzer.duty(0)
    else:
        buzzer.freq(freq)
        buzzer.duty(512)   # 50% duty = son neutre
    time.sleep_ms(duree_ms)
    buzzer.duty(0)
    time.sleep_ms(30)      # silence entre les notes

def jouer_melodie(melodie):
    print("  ♪ lecture...")
    for nom, duree in melodie:
        freq = NOTES.get(nom, 0)
        jouer_note(freq, duree)
        # Bouton mode = interrompre
        if bp_m.value() == 0:
            buzzer.duty(0)
            return

# --- Boucle principale ---
MODES = ["Clavier libre", "Jouer mélodie"]
mode  = 0
t_btn = time.ticks_ms()

print("Clavier musical prêt !")
print("Mode : Clavier libre")
print("BP1=Do  BP2=Mi  BP3=Sol  BP4=Do+  BOOT=changer mode")

while True:
    now = time.ticks_ms()

    # --- Changement de mode ---
    if bp_m.value() == 0 and time.ticks_diff(now, t_btn) > 400:
        t_btn = now
        if mode == 0:
            mode = 1
            print(f"Mode : Jouer mélodie — {MELODIES[mel_idx][0]}")
        elif mode == 1:
            # Parcourir les mélodies
            mel_idx = (mel_idx + 1) % len(MELODIES)
            print(f"Mélodie : {MELODIES[mel_idx][0]}")
            # Troisième appui → retour clavier
            if mel_idx == 0:
                mode = 0
                print("Mode : Clavier libre")
        while bp_m.value() == 0:
            time.sleep_ms(20)

    # --- Mode clavier libre ---
    if mode == 0:
        for bp, nom_note in boutons_notes:
            if bp.value() == 0:
                freq = NOTES[nom_note]
                print(f"  ♪ {nom_note} ({freq} Hz)")
                buzzer.freq(freq)
                buzzer.duty(512)
                while bp.value() == 0:
                    time.sleep_ms(10)
                buzzer.duty(0)

    # --- Mode mélodie ---
    elif mode == 1:
        if any(bp.value() == 0 for bp, _ in boutons_notes):
            jouer_melodie(MELODIES[mel_idx][1])
            while any(bp.value() == 0 for bp, _ in boutons_notes):
                time.sleep_ms(20)

    time.sleep_ms(20)
