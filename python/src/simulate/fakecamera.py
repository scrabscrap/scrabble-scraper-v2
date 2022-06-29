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

import cv2
from config import config
from util import singleton

fakecamera_formatter = config.SIMULATE_PATH
fakecamera_index = 0


@singleton
class FakeCamera:

    def __init__(self) -> None:
        self.resolution = (992, 976)
        self.framerate = 1
        self.rotation = 0

    def __enter__(self):
        return self

    def __exit__(self ,type, value, traceback):
        pass
    
    def close(self) -> None:
        global fakecamera_index
        fakecamera_index = 0
        logging.debug('FakeCamera close')

    def capture_continuous(self, output, format=None, use_video_port=False, resize=None,
                           splitter_port=0, burst=False, bayer=False, **options):
        # todo simulate streamoutput
        img = cv2.imread(fakecamera_formatter.format(fakecamera_index))
        logging.debug(f"read {fakecamera_formatter.format(fakecamera_index)}")
        img = cv2.resize(img, self.resolution)
        output.write(cv2.resize(img, self.resolution))
        return img
