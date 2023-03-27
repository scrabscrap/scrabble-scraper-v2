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
import os.path
from concurrent.futures import Future
from threading import Event

import cv2
import numpy as np
from config import config
from util import Singleton

Mat = np.ndarray[int, np.dtype[np.generic]]


class CameraFile(metaclass=Singleton):  # type: ignore
    """implement a camera simulation with images files"""

    def __init__(self, formatter=None, resolution=(config.video_width, config.video_height)):
        logging.info('### init MockCamera')
        self.frame = []
        self.resolution = resolution
        if config.video_rotate:
            self.rotation = 180
        self.event = None
        self.cnt = 1
        if formatter is not None:
            self.formatter = formatter
        else:
            self.formatter = config.simulate_path
        self.img = cv2.imread(self.formatter.format(self.cnt))

    def read(self, peek=False) -> Mat:
        """read next picture (no counter increment if peek=True)"""
        self.img = cv2.imread(self.formatter.format(self.cnt))
        logging.debug(f"read {self.cnt}: {self.formatter.format(self.cnt)} with peek={peek}")
        if not peek:
            self.cnt += 1 if os.path.isfile(
                self.formatter.format(self.cnt + 1)) else 0
        return cv2.resize(self.img, self.resolution)

    def update(self, event: Event) -> None:
        """update to next picture on thread event"""
        self.event = event
        while event.wait(0.05):
            pass
        event.clear()

    def cancel(self) -> None:
        """end of video thread"""
        if self.event is not None:
            self.event.set()

    def done(self, result: Future) -> None:
        """signal end of video thread"""
        logging.info(f'done {result}')
