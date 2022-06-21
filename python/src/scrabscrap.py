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
from signal import pause

import cv2

from button import Button

def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG, format='%(asctime)s - %(module)s - %(levelname)s - %(message)s')
    # cv2.namedWindow('CV2 Windows', cv2.WINDOW_AUTOSIZE)

    Button().start()
    pause()


if __name__ == '__main__':
    main()
