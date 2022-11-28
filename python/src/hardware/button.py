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
import logging
import time
from enum import Enum
from typing import Optional

from gpiozero import Button as GpioButton

from state import State


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


class Button:
    """Handle button press and release"""

    def __init__(self) -> None:
        self.state: Optional[State] = None
        self.bounce: dict = {}
        atexit.register(self.cleanup_atexit)

    def cleanup_atexit(self) -> None:
        """cleanup at program exit"""
        # from gpiozero import Device
        # Device.pin_factory.close()  # type: ignore
        pass

    def button_pressed(self, button: GpioButton) -> None:  # callback
        """perform button press"""
        press = time.time()
        if press > self.bounce[ButtonEnum(button.pin.number).name] + 0.1:  # type: ignore
            self.state.press_button(ButtonEnum(button.pin.number).name)    # type: ignore

    def button_released(self, button: GpioButton) -> None:  # callback
        """perform button release"""
        self.bounce[ButtonEnum(button.pin.number).name] = time.time()  # type: ignore
        self.state.release_button(ButtonEnum(button.pin.number).name)  # type: ignore

    def start(self, _state: State) -> None:
        """initialize the button handler"""
        self.state = _state
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
        self.state.do_ready()
