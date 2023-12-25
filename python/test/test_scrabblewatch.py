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
import threading
import time
import unittest

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')

from config import config
from display import Display
from hardware.led import LED
from scrabblewatch import ScrabbleWatch


# noinspection PyMethodMayBeStatic
class ScrabbleWatchTestCase(unittest.TestCase):
    """Testclass ScrabbleWatch"""

    def setUp(self) -> None:
        config.is_testing = True
        return super().setUp()

    def tearDown(self) -> None:
        config.is_testing = False
        return super().tearDown()

    @classmethod
    def tearDownClass(cls):
        # Ende Test (clean up)
        LED.switch_on({})  # type: ignore
        for thread in threading.enumerate():
            if not thread.name.startswith('Main'):
                logging.debug(f'tread-name: {thread.name}')

    # @mock.patch('camera.cam', mock.MagicMock(return_value=mockcamera.MockCamera()))
    def test_timer(self):
        """test: timer"""
        display_pause = 0.1

        ScrabbleWatch.display = Display
        logging.info('without start')
        ScrabbleWatch.display.show_boot()
        time.sleep(display_pause)
        ScrabbleWatch.display.show_cam_err()
        time.sleep(display_pause)
        ScrabbleWatch.display.show_ftp_err()
        time.sleep(display_pause)
        ScrabbleWatch.display.show_ready()
        time.sleep(display_pause)
        logging.info('start player 0')
        ScrabbleWatch.start(0)
        time.sleep(display_pause)
        logging.info('pause')
        ScrabbleWatch.pause()
        time.sleep(display_pause)
        logging.info('pause mit malus')
        ScrabbleWatch.display.add_malus(0, [100, 100], [10, 10])
        ScrabbleWatch.pause()
        time.sleep(display_pause)
        logging.info('pause mit remove')
        ScrabbleWatch.display.add_remove_tiles(1, [100, 100], [10, 10])
        ScrabbleWatch.pause()
        time.sleep(display_pause)
        logging.info('resume')
        ScrabbleWatch.resume()
        time.sleep(0.5)
        logging.info('start player 1')
        ScrabbleWatch.start(1)
        time.sleep(0.5)
        logging.info('set time to 1798')
        ScrabbleWatch.time[1] = 1798
        time.sleep(1)
        logging.info('end of sleep')
        # watch.display.stop()
        # timer.cancel()
        # cam.cancel()


if __name__ == '__main__':
    unittest.main(module='test_scrabblewatch')
