"""
 This file is part of the scrabble-scraper distribution (https://github.com/scrabscrap/scrabble-scraper)
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
import platform
from enum import Enum

from gpiozero import Button as GpioButton

import state
from config import config

if platform.machine() not in ('armv7l', 'armv6l'):
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory
    Device.pin_factory = MockFactory()


class ButtonEnum(Enum):

    def __str__(self) -> str:
        return self.name

    GREEN = 16  # GPIO16 - pin 36 - Button green
    YELLOW = 17  # GPI1O7 - pin 11 - Button yellow
    RED = 26  # GPIO26 - pin 37 - Button red

    DOUBT1 = 25  # GPIO25 - pin 22 - Button doubt1
    DOUBT2 = 12  # GPIO12 - pin 32 - Button doubt1

    RESET = 23  # GPI23 - pin 16 - Button reset
    REBOOT = 18  # GPI18 - pin 12 - Button reboot
    CONFIG = 24  # GPIO24 - pin 18 - Button config


class Button:

    def button_pressed(self, button: GpioButton) -> None:  # callback
        logging.debug(f'pressed {ButtonEnum(button.pin.number)}')  # type: ignore
        state.press_button(ButtonEnum(button.pin.number).name)  # type: ignore

    def button_released(self, button: GpioButton) -> None:  # callback
        # logging.debug(f'released {ButtonEnum(button.pin.number)}')  # type: ignore
        # state.release_button(ButtonEnum(button.pin.number).name)  # type: ignore
        pass

    def start(self, MOCK_KEYBOARD=False) -> None:
        # create Buttons and configure listener
        for b in ButtonEnum:
            if b not in [ButtonEnum.RESET, ButtonEnum.REBOOT, ButtonEnum.CONFIG]:
                logging.debug(f'Button {b.name}')
                nb = GpioButton(b.value)
                nb.when_pressed = self.button_pressed
                nb.when_released = self.button_released
            else:
                logging.debug(f'when held Button {b.name}')
                nb = GpioButton(b.value)
                nb.hold_time = 3
                nb.when_held = self.button_pressed
                nb.when_released = self.button_released
        if MOCK_KEYBOARD:
            from mock import mockbutton
            logging.debug('mock keyboard activated')
            mockbutton.listen_keyboard()
        state.do_ready()

    def stop(self) -> None:
        for b in ButtonEnum:
            nb = GpioButton(b.value)
            nb.when_pressed = None
            nb.when_released = None
