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

from __future__ import annotations

import atexit
import platform

from gpiozero import LED as GpioLED, Device

if platform.machine() not in ('aarch64', 'armv7l', 'armv6l'):
    from gpiozero.pins.mock import MockFactory

    Device.pin_factory = MockFactory()


LED_GREEN_GPIO = 20  # GPIO20 - pin 38 - led green
LED_YELLOW_GPIO = 27  # GPIO27 - pin 13 - led yellow
LED_RED_GPIO = 24  # GPIO24  - pin 18 - led red


class LEDEnum:  # pylint: disable=too-few-public-methods
    """Enumeration of physical LED"""

    @classmethod
    def set(cls):
        """set enumeration value"""
        return {LEDEnum.green, LEDEnum.yellow, LEDEnum.red}

    green = GpioLED(LED_GREEN_GPIO)
    yellow = GpioLED(LED_YELLOW_GPIO)
    red = GpioLED(LED_RED_GPIO)


class LED:
    """Implementation of LED access"""

    @staticmethod
    def switch(on: set[GpioLED] | None = None, blink: set[GpioLED] | None = None) -> None:
        """switch leds on/off/blink"""
        to_turn_off = LEDEnum.set() - (on or set()) - (blink or set())
        for i in to_turn_off:
            i.off()
        for i in on or set():
            i.on()
        for i in blink or set():
            i.blink(on_time=0.5, off_time=0.5)  # type: ignore # wrong in func definition

    @staticmethod
    def switch_on(leds: set[GpioLED], switch_off: bool = True) -> None:
        """switch all leds on"""
        if switch_off:
            for i in LEDEnum.set().difference(leds):
                i.off()
        for i in leds:
            i.on()

    @staticmethod
    def blink_on(leds: set[GpioLED], switch_off: bool = True) -> None:
        """set all leds to blink"""
        if switch_off:
            for i in LEDEnum.set().difference(leds):
                i.off()
        for i in leds:
            i.blink(on_time=0.5, off_time=0.5)  # type: ignore # wrong in func definition

    @staticmethod
    def switch_off(leds: set[GpioLED]) -> None:
        """switch all LEDs off"""
        for i in leds:
            i.off()


@atexit.register
def led_cleanup_atexit() -> None:
    """ "cleanup leds atexit"""
    LED.switch_on(set())
