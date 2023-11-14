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
from threading import Event
from time import sleep

import numpy as np

from config import Config

try:
    from picamera import PiCamera  # type: ignore
    from picamera.array import PiRGBArray  # type: ignore
except ImportError:
    print('>>> no PICamera available <<<')
    from hardware.fake_picamera import PiCamera, PiRGBArray

Mat = np.ndarray[int, np.dtype[np.generic]]

_frame: np.ndarray = np.array([])
_camera = None  # pylint: disable=invalid-name
_raw_capture = None  # pylint: disable=invalid-name
_stream = None  # pylint: disable=invalid-name


def init(resolution=None, framerate=None):
    """init/config cam"""
    global _frame, _camera, _raw_capture, _stream  # pylint: disable=global-statement
    logging.info('### init PiCamera')
    _frame = np.array([])
    if _camera is None:
        _camera = PiCamera(resolution=resolution, framerate=framerate)  # type: ignore # reportUnboundVariable
    if Config.video_rotate():
        _camera.rotation = 180
    if _raw_capture is None:
        _raw_capture = PiRGBArray(_camera, size=_camera.resolution)  # type: ignore # reportUnboundVariable
    sleep(0.3)  # warmup camera
    if _stream is None:
        _stream = _camera.capture_continuous(_raw_capture, format="bgr", use_video_port=True)
    atexit.register(_atexit)


def _atexit() -> None:
    global _stream, _frame  # pylint: disable=global-statement
    logging.info('camera close')
    if _stream:
        _stream.close()  # type: ignore
    if _raw_capture:
        _raw_capture.close()  # type: ignore
    if _camera:
        _camera.close()  # type: ignore
    _frame = np.array([])
    _stream = None


def read() -> Mat:
    """read next picture"""
    return _frame  # type: ignore


def update(event: Event) -> None:
    """update to next picture on thread event"""
    global _frame  # pylint: disable=global-statement
    if _stream is None:
        init()
    for images in _stream:  # type: ignore
        _frame = images.array  # type: ignore
        _raw_capture.truncate(0)  # type: ignore
        if event.is_set():
            break
        sleep(0.05)  # reduce cpu usage
    _atexit()
    event.clear()
