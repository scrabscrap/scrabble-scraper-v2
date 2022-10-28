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
import atexit
import logging
import sys
from concurrent.futures import Future
from threading import Event
from time import sleep
from typing import Optional

import cv2
import numpy as np
from config import config
from util import Singleton

Mat = np.ndarray[int, np.dtype[np.generic]]


class CameraOpenCV(metaclass=Singleton):  # type: ignore
    """implement a camera with OpenCV"""

    def __init__(self, src: int = 0, resolution=(config.im_width, config.im_height), framerate=config.fps):
        # initialize the video camera stream and read the first frame
        logging.info('### init OpenCV VideoCapture')
        self.stream = cv2.VideoCapture(f'/dev/video{src}', cv2.CAP_V4L)
        # self.stream = cv2.VideoCapture(-1)
        if not self.stream.isOpened():
            logging.error('can not open VideoCapture')
            sys.exit()
        self.event: Optional[Event] = None
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.stream.set(cv2.CAP_PROP_FPS, framerate)
        sleep(1)
        _, self.frame = self.stream.read()
        atexit.register(self._atexit)

    def _atexit(self) -> None:
        self.stream.release()

    def update(self, event: Event) -> None:
        """update to next picture on thread event"""
        self.event = event
        # keep looping infinitely until the thread is stopped
        while True:
            valid, self.frame = self.stream.read()
            if not valid:
                logging.warning('frame not valid')
            if config.rotade:
                self.frame = cv2.rotate(self.frame, cv2.ROTATE_180)
            if event.is_set():
                break
            sleep(0.06)
        event.clear()

    def read(self) -> Mat:
        """read next picture"""
        return self.frame

    def cancel(self) -> None:
        """end of video thread"""
        if self.event is not None:
            self.event.set()

    def done(self, result: Future) -> None:
        """signal end of video thread"""
        logging.info(f'cam done {result}')
