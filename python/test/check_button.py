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

from display import Display
from hardware.button import Button
from hardware.led import LED, LEDEnum
from scrabblewatch import ScrabbleWatch
from simulate.mockcamera import MockCamera
from state import DOUBT0, DOUBT1, GREEN, REBOOT, RED, RESET, YELLOW, State

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')


class SimulateState(State):
    """Mock: simulate State"""

    def press_button(self, button: str) -> None:
        """process button press

        before sending the next event, press button will wait for self.bounce
        """
        if button == GREEN:
            LED.switch_on({LEDEnum.green})
        elif button == RED:
            LED.switch_on({LEDEnum.red})
        elif button == YELLOW:
            LED.switch_on({LEDEnum.yellow})
        elif button == DOUBT0:
            LED.blink_on({LEDEnum.green})
        elif button == DOUBT1:
            LED.blink_on({LEDEnum.red})
        elif button == RESET:
            LED.blink_on({LEDEnum.yellow})
        elif button == REBOOT:
            LED.blink_on({LEDEnum.green, LEDEnum.red})

    def release_button(self, button: str) -> None:
        pass


class CheckButtonTestCase(unittest.TestCase):
    """check physical button"""

    def test_button(self):
        """start button event handler - display LED on Button press"""
        display = Display()
        watch = ScrabbleWatch(display)
        cam = MockCamera()

        state = SimulateState(cam=cam, watch=watch)
        # start Button-Handler
        button_handler = Button()

        # set callback for Button Events
        button_handler.start(state)
        pause()


if __name__ == '__main__':
    unittest.main()
