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
from concurrent.futures import Future
from threading import Event

from config import config
# from simulate import mockcamera
from util import singleton

try:
    from picamera import PiCamera  # type: ignore
    from picamera.array import PiRGBArray
except ImportError:
    logging.warn('use mock as PiCamera')
    from simulate.fakecamera import FakeCamera as PiCamera  # type: ignore


class Camera:

    def __init__(self):
        print('### init cam')
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

    def read(self):
        return self.frame

    def update(self, ev: Event) -> None:
        self.event = ev
        for f in self.stream:
            self.frame = f.array
            self.rawCapture.truncate(0)
            if ev.is_set():
                break
        ev.clear()

    def cancel(self) -> None:
        if self.event is not None:
            self.event.set()

    def done(self, result: Future) -> None:
        print(f'cam done {result}')
