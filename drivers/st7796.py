import os
import time
import spidev
import numpy as np
from PIL.Image import Image
import lgpio

SPI_FREQ = 40000000  # SPI clock frequency
SPI_MODE = 0b00  # SPI mode (clock polarity and phase)
RST_PIN = 27
DC_PIN = 25
BL_PIN = 12

# Hardware PWM via kernel sysfs (requires dtoverlay=pwm,pin=12,func=4 in config.txt)
_PWM_CHIP = 0
_PWM_CHANNEL = 0
_PWM_PERIOD_NS = 500_000  # 2 kHz


class ST7796:
    def __init__(self) -> None:
        self.np = np
        self.width = 320
        self.height = 480
        self.size = (self.width, self.height)

        self._gpio = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self._gpio, RST_PIN, 1)  # initial high
        lgpio.gpio_claim_output(self._gpio, DC_PIN, 1)   # initial high
        self._pwm_sysfs = f"/sys/class/pwm/pwmchip{_PWM_CHIP}/pwm{_PWM_CHANNEL}"
        self._init_hw_pwm()
        self.bl_duty_cycle(100)
        # Initialize SPI
        self.spi = spidev.SpiDev(0, 0)
        self.spi.max_speed_hz = SPI_FREQ
        self.spi.mode = SPI_MODE

        self.lcd_init()

    def _init_hw_pwm(self) -> None:
        export = f"/sys/class/pwm/pwmchip{_PWM_CHIP}/export"
        if not os.path.exists(self._pwm_sysfs):
            with open(export, "w") as f:
                f.write(str(_PWM_CHANNEL))
            time.sleep(0.05)
        with open(f"{self._pwm_sysfs}/enable", "w") as f:
            f.write("0")
        with open(f"{self._pwm_sysfs}/period", "w") as f:
            f.write(str(_PWM_PERIOD_NS))
        with open(f"{self._pwm_sysfs}/duty_cycle", "w") as f:
            f.write(str(_PWM_PERIOD_NS))  # 100% initially
        with open(f"{self._pwm_sysfs}/enable", "w") as f:
            f.write("1")

    def bl_duty_cycle(self, duty: int | float) -> None:
        """Set backlight brightness (0-100%)"""
        duty_ns = int(_PWM_PERIOD_NS * max(0.0, min(100.0, float(duty))) / 100)
        with open(f"{self._pwm_sysfs}/duty_cycle", "w") as f:
            f.write(str(duty_ns))

    def digital_write(self, pin: int, value: bool) -> None:
        lgpio.gpio_write(self._gpio, pin, 1 if value else 0)

    def spi_write_byte(self, data: list[int]) -> None:
        if self.spi is not None:
            self.spi.writebytes(data)

    def command(self, cmd: int) -> None:
        self.digital_write(DC_PIN, False)
        self.spi_write_byte([cmd])

    def data(self, val: int) -> None:
        self.digital_write(DC_PIN, True)
        self.spi_write_byte([val])

    def reset(self) -> None:
        """Reset the display"""
        self.digital_write(RST_PIN, True)
        time.sleep(0.01)
        self.digital_write(RST_PIN, False)
        time.sleep(0.01)
        self.digital_write(RST_PIN, True)
        time.sleep(0.01)

    def lcd_init(self) -> None:
        self.reset()
        self.command(0x11)
        time.sleep(0.12)

        self.command(0x36)  # Memory Data Access Control MY,MX~~
        self.data(0x08)

        self.command(0x3A)
        self.data(0x05)  # 0x05:16-bit RGB565 self.data(0x66)

        self.command(0xF0)  # Command Set Control
        self.data(0xC3)

        self.command(0xF0)
        self.data(0x96)

        self.command(0xB4)
        self.data(0x01)

        self.command(0xB7)
        self.data(0xC6)

        self.command(0xC0)
        self.data(0x80)
        self.data(0x45)

        self.command(0xC1)
        self.data(0x13)  # 18  #00

        self.command(0xC2)
        self.data(0xA7)

        self.command(0xC5)
        self.data(0x0A)

        self.command(0xE8)
        self.data(0x40)
        self.data(0x8A)
        self.data(0x00)
        self.data(0x00)
        self.data(0x29)
        self.data(0x19)
        self.data(0xA5)
        self.data(0x33)

        self.command(0xE0)
        self.data(0xD0)
        self.data(0x08)
        self.data(0x0F)
        self.data(0x06)
        self.data(0x06)
        self.data(0x33)
        self.data(0x30)
        self.data(0x33)
        self.data(0x47)
        self.data(0x17)
        self.data(0x13)
        self.data(0x13)
        self.data(0x2B)
        self.data(0x31)

        self.command(0xE1)
        self.data(0xD0)
        self.data(0x0A)
        self.data(0x11)
        self.data(0x0B)
        self.data(0x09)
        self.data(0x07)
        self.data(0x2F)
        self.data(0x33)
        self.data(0x47)
        self.data(0x38)
        self.data(0x15)
        self.data(0x16)
        self.data(0x2C)
        self.data(0x32)

        self.command(0xF0)
        self.data(0x3C)

        self.command(0xF0)
        self.data(0x69)

        self.command(0x20)

        self.command(0x11)

        time.sleep(0.1)

        self.command(0x29)

    def set_windows(
        self,
        x_start: int,
        y_start: int,
        x_end: int,
        y_end: int,
        horizontal: int = 0,
    ) -> None:
        if horizontal:
            # set the X coordinates
            self.command(0x2A)
            self.data(
                x_start >> 8
            )  # Set the horizontal starting point to the high octet
            self.data(
                x_start & 0xFF
            )  # Set the horizontal starting point to the low octet
            self.data(x_end >> 8)  # Set the horizontal end to the high octet
            self.data((x_end) & 0xFF)  # Set the horizontal end to the low octet
            # set the Y coordinates
            self.command(0x2B)
            self.data(y_start >> 8)
            self.data((y_start & 0xFF))
            self.data(y_end >> 8)
            self.data((y_end) & 0xFF)
            self.command(0x2C)
        else:
            # set the X coordinates
            self.command(0x2A)
            self.data(
                x_start >> 8
            )  # Set the horizontal starting point to the high octet
            self.data(
                x_start & 0xFF
            )  # Set the horizontal starting point to the low octet
            self.data(x_end >> 8)  # Set the horizontal end to the high octet
            self.data((x_end) & 0xFF)  # Set the horizontal end to the low octet
            # set the Y coordinates
            self.command(0x2B)
            self.data(y_start >> 8)
            self.data((y_start & 0xFF))
            self.data(y_end >> 8)
            self.data((y_end) & 0xFF)
            self.command(0x2C)

    def show_image(self, image: Image) -> None:
        imwidth, imheight = image.size
        img = self.np.asarray(image)

        # RGB888 → RGB565 (big-endian)
        r = img[..., 0].astype(self.np.uint16)
        g = img[..., 1].astype(self.np.uint16)
        b = img[..., 2].astype(self.np.uint16)
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        pix = rgb565.astype(self.np.dtype(">u2")).tobytes()

        if imwidth == self.height and imheight == self.width:
            # Landscape
            self.command(0x36)
            self.data(0x78)
            self.set_windows(0, 0, self.height, self.width, 1)
        else:
            # Portrait
            self.command(0x36)
            self.data(0x48)
            self.set_windows(0, 0, self.width, self.height, 0)

        self.digital_write(DC_PIN, True)
        self.spi.writebytes2(pix)

    def show_image_partial(self, image: Image, prev_image: Image) -> None:
        """Send only the changed bounding-box region to the display (portrait mode).
        Falls back to a full refresh when no previous image is provided."""
        img_new = self.np.asarray(image)
        img_old = self.np.asarray(prev_image)

        diff = self.np.any(img_new != img_old, axis=2)
        rows = self.np.any(diff, axis=1)
        cols = self.np.any(diff, axis=0)

        if not rows.any():
            return  # Nothing changed

        y0 = int(self.np.where(rows)[0][0])
        y1 = int(self.np.where(rows)[0][-1])
        x0 = int(self.np.where(cols)[0][0])
        x1 = int(self.np.where(cols)[0][-1])

        region = img_new[y0 : y1 + 1, x0 : x1 + 1]

        r = region[..., 0].astype(self.np.uint16)
        g = region[..., 1].astype(self.np.uint16)
        b = region[..., 2].astype(self.np.uint16)
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        pix = rgb565.astype(self.np.dtype(">u2")).tobytes()

        self.command(0x36)
        self.data(0x48)  # Portrait
        self.set_windows(x0, y0, x1, y1, 0)  # x1, y1 are inclusive
        self.digital_write(DC_PIN, True)
        self.spi.writebytes2(pix)

    def clear(self) -> None:
        """Clear contents of image buffer"""
        _buffer = [0xFF] * (self.width * self.height * 2)
        self.set_windows(0, 0, self.width, self.height)
        self.digital_write(DC_PIN, True)
        self.spi.writebytes2(_buffer)
