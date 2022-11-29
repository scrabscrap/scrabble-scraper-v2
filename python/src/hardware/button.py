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
import logging
import time
from enum import Enum
from typing import Callable, Optional

from gpiozero import Button as GpioButton

from util import Singleton


class ButtonEnum(Enum):
    """Enumeration of supported Buttons"""

    def __str__(self) -> str:
        return self.name

    GREEN = 16  # GPIO16 - pin 36 - Button green
    YELLOW = 17  # GPI17 - pin 11 - Button yellow
    RED = 23  # GPIO23 - pin 16 - Button red

    DOUBT0 = 12  # GPIO12 - pin 32 - Button doubt0 (green)
    DOUBT1 = 25  # GPIO25 - pin 22 - Button doubt1 (red)

    AP = 13  # GPIO13 - pin 33 - Button ap
    RESET = 19  # GPIO19 - pin 35 - Button reset (black)
    REBOOT = 26  # GPIO26 - pin 37 - Button reboot (blue)


class Button(metaclass=Singleton):
    """Handle button press and release"""

    def __init__(self) -> None:
        self.bounce: dict = {}
        self.func_pressed: Optional[Callable] = None
        self.func_released: Optional[Callable] = None

    def button_pressed(self, button: GpioButton) -> None:  # callback
        """perform button press"""
        press = time.time()
        if press > self.bounce[ButtonEnum(button.pin.number).name] + 0.1:  # type: ignore
            if self.func_pressed:
                self.func_pressed(ButtonEnum(button.pin.number).name)    # type: ignore

    def button_released(self, button: GpioButton) -> None:  # callback
        """perform button release"""
        self.bounce[ButtonEnum(button.pin.number).name] = time.time()  # type: ignore
        if self.func_released:
            self.func_released(ButtonEnum(button.pin.number).name)  # type: ignore

    def start(self, func_pressed: Optional[Callable] = None, func_released: Optional[Callable] = None) -> None:
        """initialize the button handler"""
        self.func_pressed = func_pressed
        self.func_released = func_released
        # create Buttons and configure listener
        for button in ButtonEnum:
            if button in [ButtonEnum.GREEN, ButtonEnum.YELLOW, ButtonEnum.RED, ButtonEnum.DOUBT0, ButtonEnum.DOUBT1]:
                logging.debug(f'Button {button.name}')
                input_button = GpioButton(button.value)
                input_button.when_pressed = self.button_pressed
                input_button.when_released = self.button_released
                self.bounce[button.name] = .0
            else:
                logging.debug(f'Button {button.name} when held')
                input_button = GpioButton(button.value)
                input_button.hold_time = 3
                input_button.when_held = self.button_pressed
                input_button.when_released = self.button_released
                self.bounce[button.name] = .0
