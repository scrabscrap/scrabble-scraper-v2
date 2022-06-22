"""
 This file is part of the scrabble-scraper distribution (https://github.com/scrabscrap/scrabble-scraper)
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
import signal
from signal import pause

import cv2

from button import Button


def ctrl_exit_handler(signal_received, frame):
    # Handle any cleanup here
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)

def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG, format='%(asctime)s - %(module)s - %(levelname)s - %(message)s')
    # cv2.namedWindow('CV2 Windows', cv2.WINDOW_AUTOSIZE)

    # Tell Python to run the handler() function when SIGINT is recieved
    signal.signal(signal.SIGINT, ctrl_exit_handler) # ctlr + c
    signal.signal(signal.SIGTSTP, ctrl_exit_handler) # ctlr + z

    Button().start()
    pause()
    exit(0)


if __name__ == '__main__':
    main()
