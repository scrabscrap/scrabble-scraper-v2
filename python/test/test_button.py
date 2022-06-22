import logging
import time
import unittest
from typing import Any

import state
from config import config
from gpiozero import Device
from gpiozero.pins.mock import MockFactory
from led import LED, LEDEnum

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(module)-10s - %(levelname)s - %(message)s')

pin_blue: Any = None
pin_green: Any = None
pin_doubt1: Any = None
pin_yellow: Any = None
pin_red: Any = None
pin_doubt2: Any = None
pin_reset: Any = None
pin_reboot: Any = None
pin_config: Any = None


# noinspection PyMethodMayBeStatic
class MyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        from button import Button, ButtonEnum

        global pin_green
        global pin_doubt1
        global pin_yellow
        global pin_red
        global pin_doubt2
        global pin_reset
        global pin_reboot
        global pin_config
        global button_handler

        # set default pin factory
        Device.pin_factory = MockFactory()
        # Get a reference to mock buttons
        pin_green = Device.pin_factory.pin(ButtonEnum.GREEN.value)
        pin_doubt1 = Device.pin_factory.pin(ButtonEnum.DOUBT0.value)
        pin_yellow = Device.pin_factory.pin(ButtonEnum.YELLOW.value)
        pin_red = Device.pin_factory.pin(ButtonEnum.RED.value)
        pin_doubt2 = Device.pin_factory.pin(ButtonEnum.DOUBT1.value)
        pin_reset = Device.pin_factory.pin(ButtonEnum.RESET.value)
        pin_reboot = Device.pin_factory.pin(ButtonEnum.REBOOT.value)
        pin_config = Device.pin_factory.pin(ButtonEnum.CONFIG.value)
        button_handler = Button()
        button_handler.start(MOCK_KEYBOARD=False)
        return super().setUpClass()

    def _press_button(self, pin, wait=0.001):
        pin.drive_high()
        time.sleep(wait)
        pin.drive_low()
        logging.info(f'leds: green {LEDEnum.green.value} yellow {LEDEnum.yellow.value} '
                        f'red {LEDEnum.red.value}')


    def test_button_led(self):

        self._press_button(pin_red) # start Green, Disp0
        assert(LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(0.5)
        self._press_button(pin_green)  # S0 Red, Disp1
        assert(LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1)
        time.sleep(0.5)
        self._press_button(pin_yellow)  # P0 Yellow, Red
        assert(LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1)
        time.sleep(0.5)
        self._press_button(pin_doubt2)  # Yellow, Red, Valid Ch. Disp0
        assert(LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1)
        time.sleep(0.5)
        self._press_button(pin_yellow)  # S1 Disp1, Red
        assert(LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1)
        time.sleep(0.5)
        self._press_button(pin_red)  # S0 Disp0, Green
        assert(LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(0.5)
        self._press_button(pin_yellow)  # P0 Disp0, Yellow, Green
        assert(LEDEnum.green.value == 1 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0)
        time.sleep(0.5)
        self._press_button(pin_doubt2)  # P0 Disp0 -10, Yellow, Green
        assert(LEDEnum.green.value == 1 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0)
        time.sleep(0.5)
        self._press_button(pin_yellow)  # S0 Disp0, Green
        assert(LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(0.5)
        self._press_button(pin_yellow)  # P0 Disp0, Yellow, Green
        assert(LEDEnum.green.value == 1 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0)
        time.sleep(0.5)
        self._press_button(pin_red)  # S0 Disp0, Green
        assert(LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(0.5)

        self._press_button(pin_yellow)  # P0 Disp0, Yellow, Green
        assert(LEDEnum.green.value == 1 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 0)
        time.sleep(0.5)

        self._press_button(pin_reset)  # Reset Game => START
        time.sleep(3.5)  # wait for held
        assert(LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)

        self._press_button(pin_red) # start Green, Disp0
        assert(LEDEnum.green.value == 1 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 0)
        time.sleep(0.5)
        self._press_button(pin_green)  # S0 Red, Disp1
        assert(LEDEnum.green.value == 0 and LEDEnum.yellow.value == 0 and LEDEnum.red.value == 1)
        time.sleep(0.5)
        self._press_button(pin_yellow)  # P0 Yellow, Red
        assert(LEDEnum.green.value == 0 and LEDEnum.yellow.value == 1 and LEDEnum.red.value == 1)
        time.sleep(0.5)

        # Ende Test
        LED.switch_on({})
        state.watch.timer.stop()
        state.watch.display.stop()

    def test_if_true(self):
        pass


if __name__ == '__main__':
    unittest.main()
