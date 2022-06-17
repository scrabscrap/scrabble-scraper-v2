import logging
import time
from typing import Any
import unittest

from gpiozero import Device
from gpiozero.pins.mock import MockFactory
from led import LED, LEDEnum
from config import config

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(module)s - %(levelname)s - %(message)s')

pin_blue: Any = None
pin_green: Any = None
pin_yellow: Any = None
pin_red: Any = None
pin_reset: Any = None
pin_reboot: Any = None
pin_config: Any = None


# noinspection PyMethodMayBeStatic
class MyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        from button import Button, ButtonEnum

        global pin_green
        global pin_yellow
        global pin_red
        global pin_reset
        global pin_reboot
        global pin_config
        # set default pin factory
        Device.pin_factory = MockFactory()
        # Get a reference to mock buttons
        pin_green = Device.pin_factory.pin(ButtonEnum.GREEN.value)
        pin_yellow = Device.pin_factory.pin(ButtonEnum.YELLOW.value)
        pin_red = Device.pin_factory.pin(ButtonEnum.RED.value)
        pin_reset = Device.pin_factory.pin(ButtonEnum.RESET.value)
        pin_reboot = Device.pin_factory.pin(ButtonEnum.REBOOT.value)
        pin_config = Device.pin_factory.pin(ButtonEnum.CONFIG.value)
        button_handler = Button()
        button_handler.start(MOCK_KEYBOARD=False)
        return super().setUpClass()

    def test_button_led(self):
        for i in range(3):  # now try to signal sensor
            pin_green.drive_high()
            time.sleep(0.01)
            pin_green.drive_low()
            logging.info(f'leds: green {LEDEnum.green.value} red {LEDEnum.red.value} '
                         f'yellow {LEDEnum.yellow.value}')

            pin_red.drive_high()
            time.sleep(0.01)
            pin_red.drive_low()
            logging.info(f'leds: green {LEDEnum.green.value} red {LEDEnum.red.value} '
                         f'yellow {LEDEnum.yellow.value}')

        time.sleep(3)
        logging.info(f'leds: green {LEDEnum.green.value} red {LEDEnum.red.value} '
                     f'yellow {LEDEnum.yellow.value}')

        pin_yellow.drive_high()
        time.sleep(0.01)
        pin_yellow.drive_low()
        logging.info(f'leds: green {LEDEnum.green.value} red {LEDEnum.red.value} '
                     f'yellow {LEDEnum.yellow.value}')

        pin_reboot.drive_high()
        logging.info('wait 3s')
        time.sleep(config.HOLD1+0.2)
        pin_reboot.drive_low()
        logging.info(f'leds: green {LEDEnum.green.value} red {LEDEnum.red.value} '
                     f'yellow {LEDEnum.yellow.value}')
        time.sleep(config.HOLD1+0.5)

    def test_if_true(self):
        pass


if __name__ == '__main__':
    unittest.main()
