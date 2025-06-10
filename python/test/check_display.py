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
import os
import unittest
from time import sleep

try:
    os.stat('/dev/i2c-1')
    from hardware.oled import OLEDDisplay as DisplayImpl
except (FileNotFoundError, ImportError):
    logging.warning('no i2c device found or import error')
    from display import Display as DisplayImpl  # type: ignore # fallback on ImportError

from config import config
from scrabblewatch import ScrabbleWatch
from util import trace

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')
logger = logging.getLogger(__name__)


class DisplayTestCase(unittest.TestCase):
    """Test pattern for OLED Display"""

    def setUp(self) -> None:
        config.is_testing = True
        return super().setUp()

    def tearDown(self) -> None:
        config.is_testing = False
        return super().tearDown()

    @trace
    def test_display(self):
        """show different pattern on the OLED Displays"""
        ScrabbleWatch.display = DisplayImpl()

        ScrabbleWatch.display.show_boot()
        ScrabbleWatch.display.show_cam_err()
        ScrabbleWatch.display.show_ftp_err()
        ScrabbleWatch.reset()
        ScrabbleWatch.display.show_ready()

        logger.debug('start 0')
        ScrabbleWatch.start(0)
        for _ in range(30):
            ScrabbleWatch.tick()
        assert ScrabbleWatch.time[0] == 30, 'invalid time 0'
        assert ScrabbleWatch.current[0] == 30, 'invalid current 0'
        assert ScrabbleWatch.time[1] == 0, 'invalid time 1'
        assert ScrabbleWatch.current[1] == 0, 'invalid current 0'

        logger.debug('start 1')
        ScrabbleWatch.start(1)
        for _ in range(21):
            ScrabbleWatch.tick()
        assert ScrabbleWatch.time[0] == 30, 'invalid time 0'
        assert ScrabbleWatch.current[0] == 0, 'invalid current 0'
        assert ScrabbleWatch.time[1] == 21, 'invalid time 1'
        assert ScrabbleWatch.current[1] == 21, 'invalid current 0'

        logger.debug('start 0')
        ScrabbleWatch.start(0)
        for _ in range(3):
            ScrabbleWatch.tick()
        logger.debug('pause')
        ScrabbleWatch.pause()
        sleep(1)

        logger.debug('0: add malus')
        _, time, current = ScrabbleWatch.status()
        ScrabbleWatch.display.add_malus(0, time, current)
        sleep(1)

        logger.debug('1: remove tiles')
        _, time, current = ScrabbleWatch.status()
        ScrabbleWatch.display.add_remove_tiles(1, time, current)
        sleep(1)

        logger.debug('0: remove tiles')
        _, time, current = ScrabbleWatch.status()
        ScrabbleWatch.display.add_doubt_timeout(1, time, current)
        sleep(1)

        logger.debug('resume')
        ScrabbleWatch.resume()

        logger.debug('start 1')
        ScrabbleWatch.start(1)
        for _ in range(2):
            ScrabbleWatch.tick()
        logger.debug('pause')
        ScrabbleWatch.pause()
        sleep(1)

        logger.debug('1: add malus')
        _, time, current = ScrabbleWatch.status()
        ScrabbleWatch.display.add_malus(1, time, current)
        sleep(1)

        logger.debug('0: remove tiles')
        _, time, current = ScrabbleWatch.status()
        ScrabbleWatch.display.add_remove_tiles(0, time, current)
        sleep(1)

        logger.debug('resume')
        ScrabbleWatch.resume()

        logger.debug('overtime')
        ScrabbleWatch.time = (1798, 1795)
        ScrabbleWatch.start(0)
        for _ in range(10):
            ScrabbleWatch.tick()
        sleep(1)

        ScrabbleWatch.start(1)
        for _ in range(10):
            ScrabbleWatch.tick()
        sleep(2)


if __name__ == '__main__':
    unittest.main(module='check_display')
