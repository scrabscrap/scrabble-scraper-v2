import logging
import signal
from signal import pause
from unittest import mock
from oled import PlayerDisplay

import cv2

from button import Button
from state import State
import time
from scrabblewatch import ScrabbleWatch
logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')

from simulate import mockvideo, mockdisplay

@mock.patch('threadvideo.VideoThread', mock.MagicMock(return_value=mockvideo.VideoSimulate()))
@mock.patch('scrabblewatch.PlayerDisplay', mock.MagicMock(return_value=mockdisplay.PlayerDisplay()))
def main() -> None:
    # cv2.namedWindow('CV2 Windows', cv2.WINDOW_AUTOSIZE)

    # Start VideoThread

    display_pause = 0.01
    watch = ScrabbleWatch()
    print(watch.display.__class__)

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
    watch.display.stop()

    # # State Machine
    # state = State()
    # # Input Event
    # Button(state).start(MOCK_KEYBOARD=True)
    # # Run until Exit
    # pause()
    # signal.alarm(0)
    # exit(0)


if __name__ == '__main__':
    main()
