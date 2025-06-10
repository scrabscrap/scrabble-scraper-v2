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
import unittest
from signal import pause

from hardware.button import ButtonEnum

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')

# ruff: noqa: E402
from config import config
from display import Display
from hardware import camera
from hardware.led import LED, LEDEnum
from scrabblewatch import ScrabbleWatch
from state import State

logger = logging.getLogger(__name__)


class SimulateState(State):
    """Mock: simulate State"""

    @classmethod
    def init(cls) -> None:
        """init state machine"""
        cls.button_handler.start(func_pressed=cls.press_button)

    @classmethod
    def press_button(cls, button: str) -> None:
        """process button press

        before sending the next event, press button will wait for self.bounce
        """
        if button == ButtonEnum.GREEN.name:
            logger.info('pressed green')
            LED.switch_on({LEDEnum.green})
        elif button == ButtonEnum.RED.name:
            logger.info('pressed red')
            LED.switch_on({LEDEnum.red})
        elif button == ButtonEnum.YELLOW.name:
            logger.info('pressed yellow')
            LED.switch_on({LEDEnum.yellow})
        elif button == ButtonEnum.DOUBT0.name:
            logger.info('pressed doubt0 (switch green)')
            LED.blink_on({LEDEnum.green})
        elif button == ButtonEnum.DOUBT1.name:
            logger.info('pressed doubt1 (switch red)')
            LED.blink_on({LEDEnum.red})
        elif button == ButtonEnum.RESET.name:
            logger.info('pressed end')
            LED.blink_on({LEDEnum.green, LEDEnum.yellow})
        elif button == ButtonEnum.REBOOT.name:
            logger.info('pressed reboot')
            LED.blink_on({LEDEnum.yellow, LEDEnum.red})
        elif button == ButtonEnum.AP.name:
            logger.info('pressed ap')
            LED.blink_on({LEDEnum.green, LEDEnum.red})


class CheckButtonTestCase(unittest.TestCase):
    """check physical button"""

    def setUp(self) -> None:
        config.is_testing = True
        return super().setUp()

    def tearDown(self) -> None:
        config.is_testing = False
        return super().tearDown()

    def test_button(self):
        """start button event handler - display LED on Button press"""
        ScrabbleWatch.display = Display()
        camera.switch_camera('file')

        # SimulateState.cam = camera.cam
        SimulateState.init()
        pause()


if __name__ == '__main__':
    unittest.main(module='check_button')
