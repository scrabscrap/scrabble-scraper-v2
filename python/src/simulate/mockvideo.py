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
import os.path

import cv2
from config import config


class VideoSimulate:

    def __init__(self, width=config.IM_WIDTH, height=config.IM_HEIGHT, formatter=None):
        self.name = 'VideoSimulate'
        self.stopped = False
        self.resolution = (width, height)
        self.frame = []
        self.cnt = 0
        if formatter is not None:
            self.formatter = formatter
        else:
            self.formatter=config.SIMULATE_PATH
        self.img = cv2.imread(self.formatter.format(self.cnt))

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def read(self):
        self.cnt += 1 if os.path.isfile(
            self.formatter.format(self.cnt + 1)) else 0
        self.img = cv2.imread(self.formatter.format(self.cnt))
        logging.debug(f"read {self.formatter.format(self.cnt)}")
        return cv2.resize(self.img, self.resolution)

    # def picture(self):
    #     _capture = PiRGBArray(self.camera, size=(IM_WIDTH, IM_HEIGHT))
    #     self.camera.capture(_capture, format="bgr")
    #     return _capture.array

    def update(self) -> None:
        pass
