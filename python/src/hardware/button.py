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

import logging
import time
from enum import Enum
from typing import Callable

from gpiozero import Button as GpioButton

from util import Static

logger = logging.getLogger()


class ButtonEnum(Enum):
    """Enumeration of supported Buttons"""

    def __str__(self) -> str:
        return self.name

    GREEN = 16  # GPIO16 - pin 36 - Button green
    YELLOW = 17  # GPI17 - pin 11 - Button yellow
    RED = 23  # GPIO23 - pin 16 - Button red

    DOUBT0 = 12  # GPIO12 - pin 32 - Button doubt0 (green)
    DOUBT1 = 25  # GPIO25 - pin 22 - Button doubt1 (red)

    AP = 13  # GPIO13 - pin 33 - Button ap (black)
    RESET = 19  # GPIO19 - pin 35 - Button reset (yellow)
    REBOOT = 26  # GPIO26 - pin 37 - Button reboot (white)


class Button(Static):
    """Handle button press and release"""

    bounce: dict = {}
    func_pressed: Callable | None = None
    func_released: Callable | None = None

    @classmethod
    def button_pressed(cls, button: GpioButton) -> None:  # callback
        """perform button press"""
        press = time.time()
        if button.pin and press > cls.bounce[ButtonEnum(button.pin.number).name] + 0.1 and cls.func_pressed:
            cls.func_pressed(ButtonEnum(button.pin.number).name)  # pylint: disable=not-callable

    @classmethod
    def button_released(cls, button: GpioButton) -> None:  # pragma: no cover  # currently not used callback
        """perform button release"""
        if button.pin:
            cls.bounce[ButtonEnum(button.pin.number).name] = time.time()
            if cls.func_released:
                cls.func_released(ButtonEnum(button.pin.number).name)  # pylint: disable=not-callable

    @classmethod
    def start(cls, func_pressed: Callable | None = None, func_released: Callable | None = None) -> None:
        """initialize the button handler"""
        cls.func_pressed = func_pressed
        cls.func_released = func_released
        # create Buttons and configure listener
        for button in ButtonEnum:
            if button in [ButtonEnum.GREEN, ButtonEnum.YELLOW, ButtonEnum.RED, ButtonEnum.DOUBT0, ButtonEnum.DOUBT1]:
                logger.debug(f'Button {button.name}')
                input_button = GpioButton(button.value)
                input_button.when_pressed = cls.button_pressed
            else:
                logger.debug(f'Button {button.name} when held')
                input_button = GpioButton(button.value)
                input_button.hold_time = 3
                input_button.when_held = cls.button_pressed

            cls.bounce[button.name] = 0.0
            input_button.when_released = cls.button_released
