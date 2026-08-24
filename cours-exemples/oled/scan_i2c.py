from machine import I2C, Pin

i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
devices = i2c.scan()

if devices:
    for d in devices:
        print(f"Trouvé : 0x{d:02X} ({d})")
else:
    print("Aucun appareil I2C trouvé — vérifie le câblage SCL/SDA")
