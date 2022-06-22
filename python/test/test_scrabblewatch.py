import logging
import time
import unittest
import state
from led import LED
import threading

from scrabblewatch import ScrabbleWatch


# noinspection PyMethodMayBeStatic
class MyTestCase(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        # Ende Test (clean up)
        # state.do_reset()
        LED.switch_on({})  # type: ignore
        state.watch.timer.stop()
        state.watch.display.stop()

    def test_timer(self):
        display_pause = 0.1

        logging.basicConfig(
            level=logging.DEBUG, format='%(asctime)s - %(funcName)10s - %(levelname)s - %(message)s')

        watch = ScrabbleWatch()
        logging.info('without start')
        watch.display.show_boot()
        time.sleep(display_pause)
        watch.display.show_cam_err()
        time.sleep(display_pause)
        watch.display.show_ftp_err()
        time.sleep(display_pause)
        watch.display.show_config()
        time.sleep(display_pause)
        watch.display.show_ready()
        time.sleep(display_pause)
        logging.info('start player 0')
        watch.start(0)
        time.sleep(display_pause)
        logging.info('pause')
        watch.pause()
        time.sleep(display_pause)
        logging.info('pause mit malus')
        watch.display.add_malus(0)
        watch.pause()
        time.sleep(display_pause)
        logging.info('pause mit remove')
        watch.display.add_remove_tiles(1)
        watch.pause()
        time.sleep(display_pause)
        logging.info('resume')
        watch.resume()
        time.sleep(2)
        logging.info('start player 1')
        watch.start(1)
        time.sleep(2)
        logging.info('set time to 1798')
        watch.time[1] = 1798
        time.sleep(4)
        logging.info('end of sleep')


if __name__ == '__main__':
    unittest.main()
