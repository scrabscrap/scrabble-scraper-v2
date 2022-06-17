import logging
import time
import unittest

from scrabblewatch import ScrabbleWatch


# noinspection PyMethodMayBeStatic
class MyTestCase(unittest.TestCase):
    def test_timer(self):
        logging.basicConfig(
            level=logging.DEBUG, format='%(asctime)s - %(module)s - %(levelname)s - %(message)s')

        watch = ScrabbleWatch()
        logging.info('without start')
        watch.display.show_boot()
        time.sleep(1)
        watch.display.show_cam_err()
        time.sleep(1)
        watch.display.show_ftp_err()
        time.sleep(1)
        watch.display.show_config()
        time.sleep(1)
        watch.display.show_ready()
        time.sleep(4)
        logging.info('start player 0')
        watch.start(0)
        time.sleep(1.5)
        logging.info('pause')
        watch.pause()
        time.sleep(1)
        logging.info('pause mit malus')
        watch.display.add_malus(0)
        watch.pause()
        time.sleep(1)
        logging.info('pause mit remove')
        watch.display.add_remove_tiles(0)
        watch.pause()
        time.sleep(1)
        logging.info('resume')
        watch.resume()
        time.sleep(2)
        logging.info('start player 1')
        watch.start(1)
        time.sleep(2)
        logging.info('set time to 1798')
        watch.time[1] = 1798
        time.sleep(4)
        watch.timer.stop()


if __name__ == '__main__':
    unittest.main()
