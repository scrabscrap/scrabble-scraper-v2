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
import platform
from concurrent.futures import Future
from enum import Enum
from threading import Event

import numpy as np
from config import config
from util import Singleton

Mat = np.ndarray[int, np.dtype[np.generic]]


class CameraEnum(Enum):
    AUTO = 1
    PICAMERA = 2
    OPENCV = 3
    FILE = 4


class Camera(metaclass=Singleton):  # type: ignore

    def __init__(self, src: int = 0, use_camera: CameraEnum = CameraEnum.AUTO, resolution=(config.im_width, config.im_height),
                 framerate=config.fps, **kwargs):
        machine = platform.machine()
        if (use_camera == CameraEnum.PICAMERA) or (use_camera == CameraEnum.AUTO and machine in ('armv7l', 'armv6l')):
            from .camera_rpi import CameraRPI
            self.stream = CameraRPI(resolution=resolution, framerate=framerate, **kwargs)
        elif (use_camera == CameraEnum.OPENCV) or (use_camera == CameraEnum.AUTO and machine in ('aarch64')):
            from .camera_opencv import CameraOpenCV
            self.stream = CameraOpenCV(src=src, resolution=resolution, framerate=framerate)
        elif (use_camera == CameraEnum.FILE) or (use_camera == CameraEnum.AUTO):
            from .camera_file import CameraFile
            self.stream = CameraFile()

    def update(self, ev: Event) -> None:
        self.stream.update(ev)

    def read(self, peek=False) -> Mat:
        from .camera_file import CameraFile
        if isinstance(self.stream, CameraFile):
            return self.stream.read(peek=peek)
        else:
            return self.stream.read()

    def cancel(self) -> None:
        self.stream.cancel()

    def done(self, result: Future) -> None:
        self.stream.done(result)
