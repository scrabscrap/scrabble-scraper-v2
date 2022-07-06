import logging
import time
import unittest

from led import LED, LEDEnum

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')


class LedTestCase(unittest.TestCase):

    def test_led(self):
        LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        logging.debug('led on')
        time.sleep(2)

        LED.switch_on({})  # type: ignore
        logging.debug('led off')
        time.sleep(2)

        LED.blink_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        logging.debug('led blink')
        time.sleep(4)

        LED.switch_on({})  # type: ignore
        logging.debug('led off')
        time.sleep(2)

        LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        logging.debug('led on')
        time.sleep(2)

        logging.debug('end')


if __name__ == '__main__':
    unittest.main()
