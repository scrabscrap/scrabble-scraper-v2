import logging
import signal
import time
from signal import pause
from unittest import mock

import cv2
from button import Button
from oled import PlayerDisplay
from scrabblewatch import ScrabbleWatch
from simulate import mockbutton # , mockdisplay, mockvideo
from state import State

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')


#@mock.patch('threadvideo.VideoThread', mock.MagicMock(return_value=mockvideo.MockVideoThread()))
#@mock.patch('scrabblewatch.PlayerDisplay', mock.MagicMock(return_value=mockdisplay.MockDisplay()))
@mock.patch('__main__.Button', mock.MagicMock(return_value=mockbutton.MockButton()))
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
