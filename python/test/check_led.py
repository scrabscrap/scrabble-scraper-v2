import time
import unittest
from led import LEDEnum, LED


class LedTestCase(unittest.TestCase):

    def test_led(self):
        LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        print('led on')
        time.sleep(2)

        LED.switch_on({})  # type: ignore
        print('led off')
        time.sleep(2)

        LED.blink_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        print('led blink')
        time.sleep(4)

        LED.switch_on({})  # type: ignore
        print('led off')
        time.sleep(2)

        LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        print('led on')
        time.sleep(2)

        print('end')


if __name__ == '__main__':
    unittest.main()
