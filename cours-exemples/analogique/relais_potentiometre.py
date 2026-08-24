# relais_potentiometre.py — 2 relais déclenchés par seuils du potentiomètre
# -----------------------------------------------------------------------
# Potentiomètre → Pin 35   (broche centrale)
# Relais 1      → Pin 27   (seuil 1/3 de course ≈ 170)
# Relais 2      → Pin 14   (seuil 2/3 de course ≈ 340)
#
# 3 zones :
#   0  – 155  : R1 OFF  R2 OFF
#   175 – 325 : R1 ON   R2 OFF
#   345 – 511 : R1 ON   R2 ON
#
# ⚠ Module relais classique (bleu) = actif BAS → LOW = ON, HIGH = OFF
#   Si tes relais s'activent à l'envers, change ACTIF_BAS = False
# -----------------------------------------------------------------------

from machine import ADC, Pin
from time import sleep_ms

ACTIF_BAS = True   # True = module bleu (LOW=ON)   False = HIGH=ON

pot = ADC(Pin(35))
pot.atten(ADC.ATTN_11DB)
pot.width(ADC.WIDTH_9BIT)   # 0 – 511

r1 = Pin(27, Pin.OUT)
r2 = Pin(14, Pin.OUT)

# Seuils avec hystérésis (±10 pts)
R1_ON  = 175;  R1_OFF = 155
R2_ON  = 345;  R2_OFF = 325

def set_relais(pin, on):
    pin.value((0 if on else 1) if ACTIF_BAS else (1 if on else 0))

# État initial : tout OFF
set_relais(r1, False)
set_relais(r2, False)
e1 = e2 = False

print("=== 2 Relais + Potentiometre ===")
print("Pin 35 = pot   Pin 27 = R1 (1/3)   Pin 14 = R2 (2/3)")
print()

while True:
    val = pot.read()
    pct = val * 100 // 511

    # Relais 1
    if not e1 and val > R1_ON:
        set_relais(r1, True);  e1 = True
        print(f"{pct:3d}%  R1 ON   R2 {'ON ' if e2 else 'OFF'}")
    elif e1 and val < R1_OFF:
        set_relais(r1, False); e1 = False
        print(f"{pct:3d}%  R1 OFF  R2 {'ON ' if e2 else 'OFF'}")

    # Relais 2
    if not e2 and val > R2_ON:
        set_relais(r2, True);  e2 = True
        print(f"{pct:3d}%  R1 {'ON ' if e1 else 'OFF'}  R2 ON")
    elif e2 and val < R2_OFF:
        set_relais(r2, False); e2 = False
        print(f"{pct:3d}%  R1 {'ON ' if e1 else 'OFF'}  R2 OFF")

    sleep_ms(50)
