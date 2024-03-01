"""
This file is part of the scrabble-scraper-v2 distribution
(https://github.com/scrabscrap/scrabble-scraper-v2)
Copyright (c) 2022 Rainer Rohloff.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import atexit
import platform
from enum import Enum
from typing import Set

from gpiozero import LED as GpioLED, Device

if platform.machine() not in ('aarch64', 'armv7l', 'armv6l'):
    from gpiozero.pins.mock import MockFactory

    Device.pin_factory = MockFactory()


class GpioLEDEnum(Enum):
    """Enumeration of supported LED GPIO"""

    GREEN_GPIO = 20  # GPIO20 - pin 38 - led green
    YELLOW_GPIO = 27  # GPIO27 - pin 13 - led yellow
    RED_GPIO = 24  # GPIO24  - pin 18 - led red


class LEDEnum:  # pylint: disable=too-few-public-methods
    """Enumeration of physical LED"""

    @classmethod
    def set(cls):
        """set enumeration value"""
        return {LEDEnum.green, LEDEnum.yellow, LEDEnum.red}

    green = GpioLED(GpioLEDEnum.GREEN_GPIO.value)
    yellow = GpioLED(GpioLEDEnum.YELLOW_GPIO.value)
    # blue = GpioLED(GpioLEDEnum.BLUE_GPIO.value)
    red = GpioLED(GpioLEDEnum.RED_GPIO.value)


class LED:
    """Implementation of LED access"""

    def __init__(self) -> None:
        atexit.register(self.cleanup_atexit)

    def cleanup_atexit(self) -> None:
        """cleanup on allication exit"""
        LED.switch_on({})  # type: ignore
        # Device.pin_factory.close()  # type: ignore

    @staticmethod
    def switch_on(leds: Set[GpioLED], switch_off: bool = True) -> None:
        """switch all leds on"""
        if switch_off:
            for i in LEDEnum.set().difference(leds):
                i.off()
        for i in leds:
            i.on()

    @staticmethod
    def blink_on(leds: Set[GpioLED], switch_off: bool = True) -> None:
        """set all leds to blink"""
        if switch_off:
            for i in LEDEnum.set().difference(leds):
                i.off()
        for i in leds:
            i.blink(on_time=0.2, off_time=0.2)  # type: ignore

    @staticmethod
    def switch_off(leds: Set[GpioLED]) -> None:
        """switch all LEDs off"""
        for i in leds:
            i.off()
