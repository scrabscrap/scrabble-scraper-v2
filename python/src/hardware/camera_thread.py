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
import atexit
import logging
import platform
from concurrent.futures import Future
from threading import Event

import numpy as np
from config import config
from util import Singleton

Mat = np.ndarray[int, np.dtype[np.generic]]

# check for rpi 64 bit - use opencv camera
if platform.machine() in ('aarch64'):

    from time import sleep

    import cv2

    class Camera(metaclass=Singleton):  # type: ignore

        def __init__(self):
            # initialize the video camera stream and read the first frame
            logging.info('### init OpenCV VideoCapture')
            self.stream = cv2.VideoCapture(0)
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 992)
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 976)
            self.stream.set(cv2.CAP_PROP_FPS, config.FPS)
            _, self.frame = self.stream.read()
            atexit.register(self._atexit)

        def _atexit(self) -> None:
            self.stream.release()

        def update(self, ev: Event) -> None:
            self.event = ev
            # keep looping infinitely until the thread is stopped
            while True:
                _, self.frame = self.stream.read()
                if config.ROTATE:
                    self.frame = cv2.rotate(self.frame, cv2.ROTATE_180)
                if ev.is_set():
                    break
                sleep(0.06)
            ev.clear()

        def read(self) -> Mat:
            return self.frame

        def cancel(self) -> None:
            if self.event is not None:
                self.event.set()

        def done(self, result: Future) -> None:
            logging.info(f'cam done {result}')

# check for rpi 32 bit - use rpi camera
elif platform.machine() in ('armv7l', 'armv6l'):

    from picamera import PiCamera  # type: ignore
    from picamera.array import PiRGBArray

    class Camera(metaclass=Singleton):  # type: ignore

        def __init__(self):
            logging.info('### init PiCamera')
            self.frame = []
            self.camera = PiCamera()
            self.camera.resolution = (992, 976)
            self.camera.framerate = config.FPS
            self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
            self.stream = self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True)
            if config.ROTATE:
                self.camera.rotation = 180
            self.event = None
            atexit.register(self._atexit)

        def _atexit(self) -> None:
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

# no rpi
else:
    print('no camera implementation available')

    import os.path

    import cv2

    class Camera(metaclass=Singleton):  # type: ignore

        def __init__(self, formatter=None):
            logging.info('### init MockCamera')
            self.frame = []
            self.resolution = (992, 976)
            self.framerate = config.FPS
            if config.ROTATE:
                self.rotation = 180
            self.event = None
            self.cnt = 0
            if formatter is not None:
                self.formatter = formatter
            else:
                self.formatter = config.SIMULATE_PATH
            self.img = cv2.imread(self.formatter.format(self.cnt))

        def read(self):
            self.cnt += 1 if os.path.isfile(
                self.formatter.format(self.cnt + 1)) else 0
            self.img = cv2.imread(self.formatter.format(self.cnt))
            logging.debug(f"read {self.formatter.format(self.cnt)}")
            return cv2.resize(self.img, self.resolution)

        def update(self, ev: Event) -> None:
            self.event = ev
            while ev.wait(0.05):
                pass
            ev.clear()

        def cancel(self) -> None:
            if self.event is not None:
                self.event.set()

        def done(self, result: Future) -> None:
            logging.info(f'done {result}')
