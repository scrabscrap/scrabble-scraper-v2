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
from config import config
from util import Singleton


class MockCamera(metaclass=Singleton):

    def __init__(self, formatter=None):
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
        print(f'done {result}')
