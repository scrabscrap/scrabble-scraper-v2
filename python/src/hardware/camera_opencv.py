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
from threading import Event
from time import sleep
from typing import Any

import cv2
import numpy as np

from config import Config

Mat = np.ndarray[int, np.dtype[np.generic]]

_frame: np.ndarray = np.array([])
_stream: Any = None
_resolution = (Config.video_width(), Config.video_height())
_framerate = Config.video_fps()


def init(src: int = 0, resolution=(Config.video_width(), Config.video_height()), framerate=Config.video_fps()):
    """init/config cam"""
    global _stream, _resolution, _framerate  # pylint: disable=global-statement
    logging.info('### init OpenCV VideoCapture')
    _resolution = resolution
    _framerate = framerate
    _stream = cv2.VideoCapture(f'/dev/video{src}', cv2.CAP_V4L)
    # self.stream = cv2.VideoCapture(-1)
    if not _stream.isOpened():
        logging.error('can not open VideoCapture')
        sys.exit()
    _stream.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    _stream.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
    _stream.set(cv2.CAP_PROP_FPS, framerate)
    sleep(1)
    atexit.register(_atexit)


def _atexit() -> None:
    global _stream, _frame  # pylint: disable=global-statement
    _stream.release()  # type: ignore
    _frame = np.array([])
    _stream = None


def update(event: Event) -> None:
    """update to next picture on thread event"""
    global _frame  # pylint: disable=global-statement
    if _stream is None:
        init()
    # keep looping infinitely until the thread is stopped
    while True:
        valid, _frame = _stream.read()  # type: ignore
        if not valid:
            logging.warning('frame not valid')
        if Config.video_rotate():
            _frame = cv2.rotate(_frame, cv2.ROTATE_180)
        if event.is_set():
            break
        sleep(0.06)
    _atexit()
    event.clear()


def read() -> Mat:
    """read next picture"""
    return _frame  # type: ignore
