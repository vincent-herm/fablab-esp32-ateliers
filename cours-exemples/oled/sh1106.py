# Driver SH1106 OLED — MicroPython
# Compatible OLED 1.3 pouces (contrôleur SH1106)
# À copier sur l'ESP32 via Thonny (clic droit → Upload to /)

import framebuf
from time import sleep_ms

class SH1106(framebuf.FrameBuffer):

    def __init__(self, width, height, external_vcc=False):
        self.width        = width
        self.height       = height
        self.external_vcc = external_vcc
        self.pages        = height // 8
        self._buffer      = bytearray(self.pages * width)
        super().__init__(self._buffer, width, height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        self._write_cmd(0xAE)   # display off
        self._write_cmd(0xD5)   # clock div
        self._write_cmd(0x80)
        self._write_cmd(0xA8)   # multiplex
        self._write_cmd(self.height - 1)
        self._write_cmd(0xD3)   # display offset
        self._write_cmd(0x00)
        self._write_cmd(0x40)   # start line
        self._write_cmd(0xAD)   # charge pump
        self._write_cmd(0x8B if not self.external_vcc else 0x8A)
        self._write_cmd(0xA1)   # seg remap
        self._write_cmd(0xC8)   # com scan dir
        self._write_cmd(0xDA)   # com pins
        self._write_cmd(0x12)
        self._write_cmd(0x81)   # contrast
        self._write_cmd(0xFF)
        self._write_cmd(0xD9)   # precharge
        self._write_cmd(0x1F if not self.external_vcc else 0x22)
        self._write_cmd(0xDB)   # vcom deselect
        self._write_cmd(0x40)
        self._write_cmd(0xA4)   # entire display on
        self._write_cmd(0xA6)   # normal display
        self.fill(0)
        self.show()
        self._write_cmd(0xAF)   # display on

    def poweroff(self):
        self._write_cmd(0xAE)

    def poweron(self):
        self._write_cmd(0xAF)

    def sleep(self, on):
        self._write_cmd(0xAE if on else 0xAF)

    def contrast(self, contrast):
        self._write_cmd(0x81)
        self._write_cmd(contrast)

    def invert(self, invert):
        self._write_cmd(0xA7 if invert else 0xA6)

    def show(self):
        # Le SH1106 a un offset de 2 colonnes dans sa RAM interne
        for page in range(self.pages):
            self._write_cmd(0xB0 | page)        # page address
            self._write_cmd(0x02)               # col low  (offset 2)
            self._write_cmd(0x10)               # col high
            self._write_data(self._buffer[page * self.width:(page + 1) * self.width])


class SH1106_I2C(SH1106):

    def __init__(self, width, height, i2c, rst=None, addr=0x3C):
        self.i2c  = i2c
        self.addr = addr
        self.rst  = rst
        if rst is not None:
            rst.value(1)
        super().__init__(width, height)

    def _write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytes([0x00, cmd]))

    def _write_data(self, buf):
        self.i2c.writeto(self.addr, b'\x40' + bytes(buf))
