from machine import Pin, TouchPad
from time import sleep_ms

t_plus  = TouchPad(Pin(4))   # D4
t_moins = TouchPad(Pin(15))  # D15

print("Lis les valeurs — pose le doigt pour voir la diff")
print("D4   | D15")
print("-----+-----")

while True:
    print(f"{t_plus.read():4d} | {t_moins.read():4d}")
    sleep_ms(200)
