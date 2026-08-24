"""
Driver MicroPython pour ecran e-paper LilyGo T5 V2.3 - 2.13 pouces
Base sur le driver officiel LilyGo gdeh0213b73.py
- fill(0) = blanc
- fill(1) = noir
- text("Bonjour", x, y, 1) = texte noir
"""

from micropython import const
from time import sleep_ms
from machine import Pin, SPI
import framebuf

ROTATION_0   = const(0)
ROTATION_90  = const(1)
ROTATION_180 = const(2)
ROTATION_270 = const(3)

EPD_WIDTH  = const(128)
EPD_HEIGHT = const(250)

LUT_FULL_UPDATE = memoryview(bytes([
    0xA0, 0x90, 0x50, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x50, 0x90, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xA0, 0x90, 0x50, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x50, 0x90, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x0F, 0x0F, 0x00, 0x00, 0x00,
    0x0F, 0x0F, 0x00, 0x00, 0x03,
    0x0F, 0x0F, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x17, 0x41, 0xA8, 0x32, 0x50, 0x0A, 0x09,
]))

LUT_PART_UPDATE = memoryview(bytes([
    0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x0A, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x15, 0x41, 0xA8, 0x32, 0x50, 0x2C, 0x0B,
]))

SW_RESET                       = b'\x12'
DRIVER_OUTPUT_CONTROL          = b'\x01'
GATE_DRIVING_VOLTAGE_CONTROL   = b'\x03'
SOURCE_DRIVING_VOLTAGE_CONTROL = b'\x04'
DATA_ENTRY_MODE_SETTING        = b'\x11'
MASTER_ACTIVATION              = b'\x20'
DISPLAY_UPDATE_CONTROL_1       = b'\x21'
DISPLAY_UPDATE_CONTROL_2       = b'\x22'
WRITE_RAM                      = b'\x24'
WRITE_VCOM_REGISTER            = b'\x2C'
WRITE_LUT_REGISTER             = b'\x32'
SET_DUMMY_LINE_PERIOD          = b'\x3A'
SET_GATE_TIME                  = b'\x3B'
BORDER_WAVEFORM_CONTROL        = b'\x3C'
SET_RAM_X_ADDRESS_START_END    = b'\x44'
SET_RAM_Y_ADDRESS_START_END    = b'\x45'
SET_RAM_X_ADDRESS_COUNTER      = b'\x4E'
SET_RAM_Y_ADDRESS_COUNTER      = b'\x4F'
SET_ANALOG_BLOCK_CONTROL       = b'\x74'
SET_DIGITAL_BLOCK_CONTROL      = b'\x7E'
DEEP_SLEEP_MODE                = b'\x10'
TERMINATE_FRAME_READ_WRITE     = b'\xFF'


class EPD(framebuf.FrameBuffer):

    def __init__(self, spi, cs, dc, rst, busy, rotation=ROTATION_0):
        self.spi  = spi
        self.cs   = cs
        self.dc   = dc
        self.rst  = rst
        self.busy = busy

        self.spi.init()
        self.cs.init(self.cs.OUT,    value=1)
        self.dc.init(self.dc.OUT,    value=0)
        self.rst.init(self.rst.OUT,  value=0)
        self.busy.init(self.busy.IN, value=0)

        self.__rotation = rotation

        if rotation in (ROTATION_0, ROTATION_180):
            self.__width  = EPD_WIDTH
            self.__height = EPD_HEIGHT
        else:
            self.__width  = EPD_HEIGHT
            self.__height = EPD_WIDTH

        size = self.__width * self.__height // 8
        self.buffer = memoryview(bytearray(size))
        super().__init__(self.buffer, self.__width, self.__height, framebuf.MONO_HLSB)
        self.hard_reset()

    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    def _command(self, command, data=None):
        self.cs(1); self.dc(0); self.cs(0)
        self.spi.write(command)
        self.cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.cs(1); self.dc(1); self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def _wait_until_idle(self):
        while self.busy.value() == 1:
            sleep_ms(10)

    def hard_reset(self):
        self.rst(1); sleep_ms(1)
        self.rst(0); sleep_ms(10)
        self.rst(1)

    def _init(self):
        self._wait_until_idle()
        self._command(SW_RESET)
        self._wait_until_idle()
        self._command(SET_ANALOG_BLOCK_CONTROL,       b'\x54')
        self._command(SET_DIGITAL_BLOCK_CONTROL,      b'\x3B')
        self._command(DRIVER_OUTPUT_CONTROL,          b'\xF9\x00\x00')
        self._command(DATA_ENTRY_MODE_SETTING,        b'\x03')
        self._command(BORDER_WAVEFORM_CONTROL,        b'\x05')
        self._command(WRITE_VCOM_REGISTER,            b'\x50')
        self._command(GATE_DRIVING_VOLTAGE_CONTROL,   LUT_FULL_UPDATE[100:101])
        self._command(SOURCE_DRIVING_VOLTAGE_CONTROL, LUT_FULL_UPDATE[101:103])
        self._command(SET_DUMMY_LINE_PERIOD,          LUT_FULL_UPDATE[105:106])
        self._command(SET_GATE_TIME,                  LUT_FULL_UPDATE[106:107])
        self._command(WRITE_LUT_REGISTER,             LUT_FULL_UPDATE[0:100])
        self._command(DISPLAY_UPDATE_CONTROL_1,       b'\x08')
        self._wait_until_idle()

    def _init_full(self):
        self._init()
        self._command(WRITE_LUT_REGISTER,       LUT_FULL_UPDATE)
        self._command(DISPLAY_UPDATE_CONTROL_2, b'\xC0')
        self._command(MASTER_ACTIVATION)
        self._wait_until_idle()

    def _set_ram_area(self):
        self._command(SET_RAM_X_ADDRESS_START_END, b'\x00\x0F')
        self._command(SET_RAM_Y_ADDRESS_START_END, b'\x00\x00\xF9\x00')
        self._command(SET_RAM_X_ADDRESS_COUNTER,   b'\x00')
        self._command(SET_RAM_Y_ADDRESS_COUNTER,   b'\x00\x00')
        self._wait_until_idle()

    def _get_rotated_buffer(self):
        if self.__rotation == ROTATION_0:
            return self.buffer
        size  = EPD_WIDTH * EPD_HEIGHT // 8
        fbuf  = memoryview(bytearray(size))
        frame = framebuf.FrameBuffer(fbuf, EPD_WIDTH, EPD_HEIGHT, framebuf.MONO_HLSB)
        if self.__rotation == ROTATION_270:
            for x in range(self.__width):
                for y in range(self.__height):
                    frame.pixel(y, EPD_HEIGHT - x - 1, self.pixel(x, y))
        elif self.__rotation == ROTATION_90:
            for x in range(self.__width):
                for y in range(self.__height):
                    frame.pixel(EPD_WIDTH - y - 1, x, self.pixel(x, y))
            frame.scroll(-6, 0)
        elif self.__rotation == ROTATION_180:
            for i in range(size):
                fbuf[size - i - 1] = self.buffer[i]
            frame.scroll(-6, 0)
        return fbuf

    def update(self):
        self._init_full()
        self._set_ram_area()
        self._command(WRITE_RAM, self._get_rotated_buffer())
        self._command(DISPLAY_UPDATE_CONTROL_2, b'\xC7')
        self._command(MASTER_ACTIVATION)
        self._wait_until_idle()
        self._command(DISPLAY_UPDATE_CONTROL_2, b'\xC3')
        self._command(MASTER_ACTIVATION)
        self._wait_until_idle()

    def deep_sleep(self):
        self._command(DEEP_SLEEP_MODE, b'\x01')


def init_epd(rotation=ROTATION_0):
    """
    fill(0) = blanc
    fill(1) = noir
    text("Bonjour", x, y, 1) = texte noir sur blanc
    """
    spi = SPI(1, baudrate=4000000,
              sck=Pin(18),
              mosi=Pin(23))
    return EPD(spi,
               cs=Pin(5),
               dc=Pin(17),
               rst=Pin(16),
               busy=Pin(4),
               rotation=rotation)
