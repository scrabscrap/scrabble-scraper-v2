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
from concurrent.futures import Future
from threading import Event
from time import sleep

import numpy as np
from picamera import PiCamera  # type: ignore
from picamera.array import PiRGBArray

from config import config
from util import Singleton

Mat = np.ndarray[int, np.dtype[np.generic]]


class CameraRPI(metaclass=Singleton):  # type: ignore
    """implement a camera with rpi native"""

    def __init__(self, resolution=(config.video_width, config.video_height), framerate=config.video_fps):
        logging.info('### init PiCamera')
        self.frame = []
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.raw_capture = PiRGBArray(self.camera, size=self.camera.resolution)
        sleep(1)  # warmup camera
        self.stream = self.camera.capture_continuous(self.raw_capture, format="bgr", use_video_port=True)
        if config.video_rotate:
            self.camera.rotation = 180
        self.event = None
        atexit.register(self._atexit)

    def _atexit(self) -> None:
        logging.info('camera close')
        self.stream.close()  # type: ignore
        self.raw_capture.close()
        self.camera.close()

    def read(self) -> Mat:
        """read next picture"""
        return self.frame  # type: ignore

    def update(self, event: Event) -> None:
        """update to next picture on thread event"""
        self.event = event
        for images in self.stream:
            self.frame = images.array  # type: ignore
            self.raw_capture.truncate(0)
            if event.is_set():
                break
            sleep(0.05)  # reduce cpu usage
        event.clear()

    def cancel(self) -> None:
        """end of video thread"""
        if self.event is not None:
            self.event.set()

    def done(self, result: Future) -> None:
        """signal end of video thread"""
        logging.info(f'cam done {result}')
