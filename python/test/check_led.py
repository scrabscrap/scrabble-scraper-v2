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
import time
import unittest

from hardware.led import LED, LEDEnum

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')


class LedTestCase(unittest.TestCase):

    def test_led(self):
        LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        logging.debug('led on')
        time.sleep(1)

        LED.switch_on({})  # type: ignore
        logging.debug('led off')
        time.sleep(1)

        LED.blink_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        logging.debug('led blink')
        time.sleep(2)

        LED.blink_on({LEDEnum.yellow})
        logging.debug('led yellow blink')
        time.sleep(2)

        LED.switch_on({})  # type: ignore
        logging.debug('led off')
        time.sleep(1)

        LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        logging.debug('led on')
        time.sleep(1)

        LED.switch_on({LEDEnum.green})
        logging.debug('led green on')
        time.sleep(1)

        LED.switch_on({LEDEnum.yellow})
        logging.debug('led yellow on')
        time.sleep(1)

        LED.switch_on({LEDEnum.red})
        logging.debug('led yellow on')
        time.sleep(1)

        logging.debug('end')


if __name__ == '__main__':
    unittest.main()
