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
    from hardware.oled import PlayerDisplay
except (FileNotFoundError, ImportError):
    logging.warning('no i2c device found or import error')
    from display import Display as PlayerDisplay  # type: ignore # fallback on ImportError

from config import config
from scrabblewatch import ScrabbleWatch
from util import trace

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')


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
        display = PlayerDisplay()
        watch = ScrabbleWatch(display)

        watch.display.show_boot()
        watch.display.show_cam_err()
        watch.display.show_config()
        watch.display.show_ftp_err()
        watch.reset()
        watch.display.show_ready()

        logging.debug('start 0')
        watch.start(0)
        for _ in range(30):
            watch.tick()
        assert watch.time[0] == 30, 'invalid time 0'
        assert watch.current[0] == 30, 'invalid current 0'
        assert watch.time[1] == 0, 'invalid time 1'
        assert watch.current[1] == 0, 'invalid current 0'

        logging.debug('start 1')
        watch.start(1)
        for _ in range(21):
            watch.tick()
        assert watch.time[0] == 30, 'invalid time 0'
        assert watch.current[0] == 0, 'invalid current 0'
        assert watch.time[1] == 21, 'invalid time 1'
        assert watch.current[1] == 21, 'invalid current 0'

        logging.debug('start 0')
        watch.start(0)
        for _ in range(3):
            watch.tick()
        logging.debug('pause')
        watch.pause()
        sleep(1)

        logging.debug('0: add malus')
        _, time, current = watch.status()
        watch.display.add_malus(0, time, current)
        sleep(1)

        logging.debug('1: remove tiles')
        _, time, current = watch.status()
        watch.display.add_remove_tiles(1, time, current)
        sleep(1)

        logging.debug('0: remove tiles')
        _, time, current = watch.status()
        watch.display.add_doubt_timeout(1, time, current)
        sleep(1)

        logging.debug('resume')
        watch.resume()

        logging.debug('start 1')
        watch.start(1)
        for _ in range(2):
            watch.tick()
        logging.debug('pause')
        watch.pause()
        sleep(1)

        logging.debug('1: add malus')
        _, time, current = watch.status()
        watch.display.add_malus(1, time, current)
        sleep(1)

        logging.debug('0: remove tiles')
        _, time, current = watch.status()
        watch.display.add_remove_tiles(0, time, current)
        sleep(1)

        logging.debug('resume')
        watch.resume()

        logging.debug('overtime')
        watch.time[0] = 1798
        watch.time[1] = 1795
        watch.start(0)
        for _ in range(10):
            watch.tick()
        sleep(1)

        watch.start(1)
        for _ in range(10):
            watch.tick()
        sleep(2)


if __name__ == '__main__':
    unittest.main(module='check_display')
