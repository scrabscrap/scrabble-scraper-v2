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
from hardware.camera_thread import Camera, CameraEnum
from hardware.led import LED, LEDEnum
from scrabblewatch import ScrabbleWatch
from state import DOUBT0, DOUBT1, GREEN, REBOOT, RED, RESET, YELLOW, State

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')


class SimulateState(State):
    """Mock: simulate State"""

    def init(self) -> None:
        """init state machine"""
        self.button_handler.start(func_pressed=self.press_button)

    def press_button(self, button: str) -> None:
        """process button press

        before sending the next event, press button will wait for self.bounce
        """
        if button == GREEN:
            logging.info("pressed green")
            LED.switch_on({LEDEnum.green})
        elif button == RED:
            logging.info("pressed red")
            LED.switch_on({LEDEnum.red})
        elif button == YELLOW:
            logging.info("pressed yellow")
            LED.switch_on({LEDEnum.yellow})
        elif button == DOUBT0:
            logging.info("pressed doubt0 (switch green)")
            LED.blink_on({LEDEnum.green})
        elif button == DOUBT1:
            logging.info("pressed doubt1 (switch red)")
            LED.blink_on({LEDEnum.red})
        elif button == RESET:
            logging.info("pressed reset")
            LED.blink_on({LEDEnum.yellow})
        elif button == REBOOT:
            logging.info("pressed reboot")
            LED.blink_on({LEDEnum.green, LEDEnum.red})


class CheckButtonTestCase(unittest.TestCase):
    """check physical button"""

    def test_button(self):
        """start button event handler - display LED on Button press"""
        display = Display()
        watch = ScrabbleWatch(display)
        cam = Camera(use_camera=CameraEnum.FILE)

        state = SimulateState(cam=cam, watch=watch)
        state.init()
        pause()


if __name__ == '__main__':
    unittest.main()
