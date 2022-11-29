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
import logging.config
import os
import time
import unittest

logging.config.fileConfig(fname=os.path.dirname(os.path.abspath(__file__)) + '/test_log.conf',
                          disable_existing_loggers=False)


from time import sleep

from gpiozero import Device
from gpiozero.pins.mock import MockFactory

from display import Display
from hardware.button import ButtonEnum
from hardware.led import LED, LEDEnum
from hardware.camera_file import CameraFile
from scrabblewatch import ScrabbleWatch
from state import State


class ButtonTestCase(unittest.TestCase):
    """Test class button"""

    def config_setter(self, section: str, option: str, value):
        """set scrabble config"""
        from config import config

        if value is not None:
            if section not in config.config.sections():
                config.config.add_section(section)
            config.config.set(section, option, str(value))
        else:
            config.config.remove_option(section, option)

    def setUp(self) -> None:
        self.config_setter('output', 'ftp', False)
        self.config_setter('output', 'web', False)

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
        # self.pin_config = Device.pin_factory.pin(ButtonEnum.CONFIG.value)
        display = Display()
        watch = ScrabbleWatch(display)

        cam = CameraFile()
        cam.cnt = 0
        self.state = State(cam=cam, watch=watch)
        self.state.cam = cam  # reapply cam and watch because of singleton
        self.state.watch = watch
        self.state.init()
        return super().setUp()

    def tearDown(self) -> None:
        self.state.do_reset()
        LED.switch_on({})  # type: ignore
        Device.pin_factory.reset()  # type: ignore
        # for thread in threading.enumerate():
        #    if not thread.name.startswith('Main'):
        #        logging.debug(f'thread: {thread.name}')
        # timer.cancel()
        return super().tearDown()

    def _press_button(self, pin, wait=0.1):
        """press button on MockFactory Button

            pin: button pin to press
            wait: wait between press and release - should be greater than bounce time in state.press_button()
        """
        logging.info(f'press button {pin}')
        pin.drive_high()
        time.sleep(wait)
        pin.drive_low()

        if self.state.last_submit is not None:
            while not self.state.last_submit.done():  # type: ignore
                sleep(0.1)
        logging.info(f'leds: green {LEDEnum.green.value} yellow {LEDEnum.yellow.value} '
                     f'red {LEDEnum.red.value} state nw {State().current_state}')

    def test_doubt01(self):
        """Test doubt01"""
        # doubt invalid
        display_pause = 0.01
        self.state.do_ready()

        time.sleep(display_pause)
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0

        self._press_button(self.pin_red)  # start Green, Disp0
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_green)  # S0 Red, Disp1
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1
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
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0

        self._press_button(self.pin_red)  # start Green, Disp0
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_green)  # S0 Red, Disp1
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1
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
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0

        self._press_button(self.pin_red)  # start Green, Disp0
        time.sleep(display_pause)
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
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
        assert State().current_state == 'S0'
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_green)  # S0 Red, Disp1
        assert State().current_state == 'S1'
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert State().current_state == 'P1'
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_doubt1)  # P0 Yellow, Red, Valid Ch. Disp0
        assert State().current_state == 'P1'
        # yellow is in state blink
        assert LEDEnum.green.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # S1 Disp1, Red
        assert State().current_state == 'S1'
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_red)  # S0 Disp0, Green
        assert State().current_state == 'S0'
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Disp0, Yellow, Green
        assert State().current_state == 'P0'
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_doubt1)  # P0 Disp0 -10, Yellow, Green
        assert State().current_state == 'P0'
        # yellow is in state blink
        assert LEDEnum.green.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # S0 Disp0, Green
        assert State().current_state == 'S0'
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Disp0, Yellow, Green
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_red)  # S0 Disp0, Green
        assert State().current_state == 'S0'
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Disp0, Yellow, Green
        assert State().current_state == 'P0'
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        State().do_reset()
        assert State().current_state == 'START'
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0

        self._press_button(self.pin_red)  # S1 start Green, Disp0
        assert State().current_state == 'S0'
        assert LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0
        time.sleep(display_pause)

        self._press_button(self.pin_green)  # S1 Red, Disp1
        assert State().current_state == 'S1'
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert State().current_state == 'P1'
        assert LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1
        time.sleep(display_pause)


if __name__ == '__main__':
    unittest.main()
