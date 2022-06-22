import logging
import time
import unittest
import state
from led import LED

from scrabblewatch import ScrabbleWatch


# noinspection PyMethodMayBeStatic
class MyTestCase(unittest.TestCase):

    @classmethod
    def tearDownClass(self):
        # Ende Test (clean up)
        state.do_reset()
        LED.switch_on({})
        state.watch.timer.stop()
        state.watch.display.stop()

    def test_timer(self):
        logging.basicConfig(
            level=logging.DEBUG, format='%(asctime)s - %(funcName)10s - %(levelname)s - %(message)s')

        watch = ScrabbleWatch()
        logging.info('without start')
        watch.display.show_boot()
        time.sleep(0.5)
        watch.display.show_cam_err()
        time.sleep(0.5)
        watch.display.show_ftp_err()
        time.sleep(0.5)
        watch.display.show_config()
        time.sleep(0.5)
        watch.display.show_ready()
        time.sleep(0.5)
        logging.info('start player 0')
        watch.start(0)
        time.sleep(0.5)
        logging.info('pause')
        watch.pause()
        time.sleep(0.5)
        logging.info('pause mit malus')
        watch.display.add_malus(0)
        watch.pause()
        time.sleep(0.5)
        logging.info('pause mit remove')
        watch.display.add_remove_tiles(1)
        watch.pause()
        time.sleep(0.5)
        logging.info('resume')
        watch.resume()
        time.sleep(2)
        logging.info('start player 1')
        watch.start(1)
        time.sleep(2)
        logging.info('set time to 1798')
        watch.time[1] = 1798
        time.sleep(4)


if __name__ == '__main__':
    unittest.main()
