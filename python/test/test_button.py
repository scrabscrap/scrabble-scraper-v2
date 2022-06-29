import logging
import threading
import time
import unittest
from typing import Any

from button import Button, ButtonEnum
from config import config
from gpiozero import Device
from gpiozero.pins.mock import MockFactory
from led import LED, LEDEnum
from state import State
from scrabblewatch import timer

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')


class ButtonTestCase(unittest.TestCase):

    def setUp(self) -> None:
        # set default pin factory
        Device.pin_factory = MockFactory()
        # Get a reference to mock buttons
        self.pin_green = Device.pin_factory.pin(ButtonEnum.GREEN.value)
        self.pin_doubt1 = Device.pin_factory.pin(ButtonEnum.DOUBT0.value)
        self.pin_yellow = Device.pin_factory.pin(ButtonEnum.YELLOW.value)
        self.pin_red = Device.pin_factory.pin(ButtonEnum.RED.value)
        self.pin_doubt2 = Device.pin_factory.pin(ButtonEnum.DOUBT1.value)
        self.pin_reset = Device.pin_factory.pin(ButtonEnum.RESET.value)
        self.pin_reboot = Device.pin_factory.pin(ButtonEnum.REBOOT.value)
        self.pin_config = Device.pin_factory.pin(ButtonEnum.CONFIG.value)
        self.state = State()
        self.button_handler = Button()
        self.button_handler.start(self.state)
        return super().setUp()

    def tearDown(self) -> None:
        self.state.do_reset()
        LED.switch_on({})  # type: ignore
        self.state.watch.display.stop()
        Device.pin_factory.reset()  # type: ignore
        for thread in threading.enumerate():
            if not thread.name.startswith('Main'):
                print(thread.name)
        timer.cancel()
        return super().tearDown()

    def _press_button(self, pin, wait=0.001):
        pin.drive_high()
        time.sleep(wait)
        pin.drive_low()
        logging.info(f'leds: green {LEDEnum.green.value} yellow {LEDEnum.yellow.value} '
                     f'red {LEDEnum.red.value}')

    def test_doubt(self):
        display_pause = 0.01

        self.state.do_reset()
        time.sleep(display_pause)
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        self._press_button(self.pin_red)  # start Green, Disp0
        assert(LEDEnum.green.value == 1 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_green)  # S0 Red, Disp1
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1)
        time.sleep(display_pause)
        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1)
        time.sleep(display_pause)
        self._press_button(self.pin_doubt1)  # Yellow, Red, invalid Ch. Disp1
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1)
        time.sleep(display_pause)
        self._press_button(self.pin_doubt2)  # Yellow, Red, Valid Ch. Disp0
        time.sleep(display_pause)
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1)

        self.state.do_reset()
        time.sleep(display_pause)
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        self._press_button(self.pin_red)  # start Green, Disp0
        assert(LEDEnum.green.value == 1 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert(LEDEnum.green.value == 1 and LEDEnum.yellow.value ==
               1 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_doubt1)  # Yellow, Red, invalid Ch. Disp1
        assert(LEDEnum.green.value == 1 and
               LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_doubt2)  # Yellow, Red, Valid Ch. Disp0
        assert(LEDEnum.green.value == 1
               and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0)
        time.sleep(display_pause)

    def test_button_led(self):
        display_pause = 0.01

        self.state.do_reset()
        self._press_button(self.pin_red)  # start Green, Disp0
        assert(LEDEnum.green.value == 1 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_green)  # S0 Red, Disp1
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1)
        time.sleep(display_pause)
        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1)
        time.sleep(display_pause)
        self._press_button(self.pin_doubt2)  # Yellow, Red, Valid Ch. Disp0
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1)
        time.sleep(display_pause)
        self._press_button(self.pin_yellow)  # S1 Disp1, Red
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1)
        time.sleep(display_pause)
        self._press_button(self.pin_red)  # S0 Disp0, Green
        assert(LEDEnum.green.value == 1 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_yellow)  # P0 Disp0, Yellow, Green
        assert(LEDEnum.green.value == 1
               and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_doubt2)  # P0 Disp0 -10, Yellow, Green
        assert(LEDEnum.green.value == 1
               and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_yellow)  # S0 Disp0, Green
        assert(LEDEnum.green.value == 1 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_yellow)  # P0 Disp0, Yellow, Green
        assert(LEDEnum.green.value == 1 and
               LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_red)  # S0 Disp0, Green
        assert(LEDEnum.green.value == 1
               and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(display_pause)

        self._press_button(self.pin_yellow)  # P0 Disp0, Yellow, Green
        assert(LEDEnum.green.value == 1 and
               LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0)
        time.sleep(display_pause)

        self._press_button(self.pin_reset)  # Reset Game => START
        logging.debug('pause for hold button (3.5s)')
        time.sleep(3.5)  # wait for held > 3s
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)

        self._press_button(self.pin_red)  # start Green, Disp0
        assert(LEDEnum.green.value == 1 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(display_pause)
        self._press_button(self.pin_green)  # S0 Red, Disp1
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1)
        time.sleep(display_pause)
        self._press_button(self.pin_yellow)  # P0 Yellow, Red
        assert(LEDEnum.green.value == 0 and
               LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1)
        time.sleep(display_pause)


if __name__ == '__main__':
    unittest.main()
