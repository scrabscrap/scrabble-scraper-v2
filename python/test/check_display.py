import logging
import time
import unittest

from hardware.oled import PlayerDisplay
from scrabblewatch import ScrabbleWatch
from util import trace

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')


class DisplayTestCase(unittest.TestCase):

    @trace
    def test_display(self):
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
        time.sleep(1)

        logging.debug('0: add malus')
        watch.display.add_malus(0)
        time.sleep(1)

        logging.debug('1: remove tiles')
        watch.display.add_remove_tiles(1)
        time.sleep(1)

        logging.debug('0: remove tiles')
        watch.display.add_doubt_timeout(1)
        time.sleep(1)

        logging.debug('resume')
        watch.resume()

        logging.debug('start 1')
        watch.start(1)
        for _ in range(2):
            watch.tick()
        logging.debug('pause')
        watch.pause()
        time.sleep(1)

        logging.debug('1: add malus')
        watch.display.add_malus(1)
        time.sleep(1)

        logging.debug('0: remove tiles')
        watch.display.add_remove_tiles(0)
        time.sleep(1)

        logging.debug('resume')
        watch.resume()

        logging.debug('overtime')
        watch.time[0] = 1798
        watch.time[1] = 1795
        watch.start(0)
        for _ in range(10):
            watch.tick()
        time.sleep(1)

        watch.start(1)
        for _ in range(10):
            watch.tick()
        time.sleep(2)


if __name__ == '__main__':
    unittest.main()
