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
import sys
import time
import unittest
from time import sleep

from gpiozero import Device
from gpiozero.pins.mock import MockFactory

from config import config
from display import Display
from hardware import camera
from hardware.button import ButtonEnum
from hardware.led import LED, LEDEnum
from scrabblewatch import ScrabbleWatch
from state import GameState, State

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, force=True, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'
)
logger = logging.getLogger(__name__)


class ButtonTestCase(unittest.TestCase):
    """Test class button"""

    def config_setter(self, section: str, option: str, value):
        """set scrabble config"""

        if value is not None:
            if section not in config.config.sections():
                config.config.add_section(section)
            config.config.set(section, option, str(value))
        else:
            config.config.remove_option(section, option)

    def setUp(self) -> None:
        self.config_setter('output', 'upload_server', False)
        config.is_testing = True

        # set default pin factory
        Device.pin_factory = MockFactory()
        # Get a reference to mock buttons
        self.pin_green = Device.pin_factory.pin(ButtonEnum.GREEN.value)
        self.pin_doubt0 = Device.pin_factory.pin(ButtonEnum.DOUBT0.value)
        self.pin_yellow = Device.pin_factory.pin(ButtonEnum.YELLOW.value)
        self.pin_red = Device.pin_factory.pin(ButtonEnum.RED.value)
        self.pin_doubt1 = Device.pin_factory.pin(ButtonEnum.DOUBT1.value)
        self.pin_reset = Device.pin_factory.pin(ButtonEnum.RESET.value)
        self.pin_reboot = Device.pin_factory.pin(ButtonEnum.REBOOT.value)
        # self.pin_config = Device.pin_factory.pin(ButtonEnum.config.value)
        ScrabbleWatch.display = Display()
        camera.switch_camera('file')
        State.init()
        return super().setUp()

    def tearDown(self) -> None:
        State.do_new_game()
        LED.switch_on({})  # type: ignore
        Device.pin_factory.reset()  # type: ignore
        config.is_testing = False
        # for thread in threading.enumerate():
        #    if not thread.name.startswith('Main'):
        #        logger.debug(f'thread: {thread.name}')
        # timer.cancel()
        return super().tearDown()

    def _press_button(self, pin, wait=0.1):
        """press button on MockFactory Button

        pin: button pin to press
        wait: wait between press and release - should be greater than bounce time in state.press_button()
        """
        logger.info(f'press button {pin}')
        pin.drive_high()
        time.sleep(wait)
        pin.drive_low()

        sleep(0.05)
        logger.info(
            f'leds: green {LEDEnum.green.value} yellow {LEDEnum.yellow.value} '
            f'red {LEDEnum.red.value} state nw {State.ctx.current_state}'
        )

    def test_doubt01(self):
        """Test doubt01"""
        # doubt invalid
        display_pause = 0.01
        State.do_ready()

        time.sleep(display_pause)
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1

        self._press_button(self.pin_red)  # start Green, Disp0
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_green)  # S0 Red, Disp1
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_doubt0)  # Yellow, Red, invalid Ch. Disp1
        # yellow is in state blink
        assert LEDEnum.green.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

    def test_doubt02(self):
        """Test doubt01"""
        # doubt valid
        display_pause = 0.01

        time.sleep(display_pause)
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1

        self._press_button(self.pin_red)  # start Green, Disp0
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_green)  # S0 Red, Disp1
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_doubt1)  # Yellow, Red, invalid Ch. Disp1
        # yellow is in state blink
        assert LEDEnum.green.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

    def test_doubt03(self):
        """Test doubt 03"""
        # first invalid challenge, second valid challenge
        display_pause = 0.01

        time.sleep(display_pause)
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1

        self._press_button(self.pin_red)  # start Green, Disp0
        time.sleep(display_pause)
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_doubt0)  # Yellow, Red, invalid Ch. Disp1
        # yellow is in state blink
        assert LEDEnum.green.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_doubt1)  # Yellow, Red, Valid Ch. Disp0
        # yellow is in state blink
        assert LEDEnum.green.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

    def test_button_led(self):
        """Test LED"""
        display_pause = 0.01

        # start
        self._press_button(self.pin_red)  # start Green, Disp0
        assert State.ctx.current_state == GameState.S0
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_green)  # S0 Red, Disp1
        assert State.ctx.current_state == GameState.S1
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert State.ctx.current_state == GameState.P1
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_doubt1)  # P0 Yellow, Red, Valid Ch. Disp0
        assert State.ctx.current_state == GameState.P1
        # yellow is in state blink
        assert LEDEnum.green.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # S1 Disp1, Red
        assert State.ctx.current_state == GameState.S1
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_red)  # S0 Disp0, Green
        assert State.ctx.current_state == GameState.S0
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Disp0, Yellow, Green
        assert State.ctx.current_state == GameState.P0
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_doubt1)  # P0 Disp0 -10, Yellow, Green
        assert State.ctx.current_state == GameState.P0
        # yellow is in state blink
        assert LEDEnum.green.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # S0 Disp0, Green
        assert State.ctx.current_state == GameState.S0
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Disp0, Yellow, Green
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_red)  # S0 Disp0, Green
        assert State.ctx.current_state == GameState.S0
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Disp0, Yellow, Green
        assert State.ctx.current_state == GameState.P0
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        State.do_new_game()
        camera.cam.counter = 1  # type: ignore
        assert State.ctx.current_state == GameState.START
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1

        self._press_button(self.pin_red)  # S1 start Green, Disp0
        assert State.ctx.current_state == GameState.S0
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_green)  # S1 Red, Disp1
        assert State.ctx.current_state == GameState.S1
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert State.ctx.current_state == GameState.P1
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

    def test_button_enum(self):
        assert str(ButtonEnum.GREEN) == 'GREEN'
        assert str(ButtonEnum.YELLOW) == 'YELLOW'
        assert str(ButtonEnum.RED) == 'RED'
        assert str(ButtonEnum.DOUBT0) == 'DOUBT0'
        assert str(ButtonEnum.DOUBT1) == 'DOUBT1'
        assert str(ButtonEnum.AP) == 'AP'
        assert str(ButtonEnum.RESET) == 'RESET'
        assert str(ButtonEnum.REBOOT) == 'REBOOT'

        assert ButtonEnum.GREEN.value == 16
        assert ButtonEnum.YELLOW.value == 17
        assert ButtonEnum.RED.value == 23
        assert ButtonEnum.DOUBT0.value == 12
        assert ButtonEnum.DOUBT1.value == 25
        assert ButtonEnum.AP.value == 13
        assert ButtonEnum.RESET.value == 19
        assert ButtonEnum.REBOOT.value == 26


if __name__ == '__main__':
    unittest.main(module='test_button')
