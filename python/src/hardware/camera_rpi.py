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

import numpy as np
from config import config
from picamera import PiCamera  # type: ignore
from picamera.array import PiRGBArray
from util import Singleton

Mat = np.ndarray[int, np.dtype[np.generic]]


class CameraRPI(metaclass=Singleton):  # type: ignore

    def __init__(self, resolution=(config.im_width, config.im_height), framerate=config.fps, **kwargs):
        logging.info('### init PiCamera')
        self.frame = []
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True)
        if config.rotade:
            self.camera.rotation = 180
        self.event = None
        atexit.register(self._atexit)

    def _atexit(self) -> None:
        logging.debug('camera close')
        self.stream.close()  # type: ignore
        self.rawCapture.close()
        self.camera.close()

    def read(self) -> Mat:
        return self.frame  # type: ignore

    def update(self, ev: Event) -> None:
        self.event = ev
        for f in self.stream:
            self.frame = f.array  # type: ignore
            self.rawCapture.truncate(0)
            if ev.is_set():
                break
        ev.clear()

    def cancel(self) -> None:
        if self.event is not None:
            self.event.set()

    def done(self, result: Future) -> None:
        logging.info(f'cam done {result}')
