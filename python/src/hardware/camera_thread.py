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
from typing import Union

import numpy as np
from config import config
from util import Singleton

from .camera_file import CameraFile
from .camera_opencv import CameraOpenCV

Mat = np.ndarray[int, np.dtype[np.generic]]


class CameraEnum(Enum):
    """Enumation of supported camera types"""
    AUTO = 1
    PICAMERA = 2
    OPENCV = 3
    FILE = 4


class Camera(metaclass=Singleton):  # type: ignore
    """implement a camera thread as proxy"""

    def __init__(self, src: int = 0, use_camera: CameraEnum = CameraEnum.AUTO,
                 resolution=(config.video_width, config.video_height), framerate=config.video_fps, **kwargs):
        machine = platform.machine()
        if (use_camera == CameraEnum.PICAMERA) or (use_camera == CameraEnum.AUTO and machine in ('armv7l', 'armv6l')):
            from .camera_rpi import CameraRPI
            self.stream: Union[CameraRPI, CameraOpenCV, CameraFile] = CameraRPI(
                resolution=resolution, framerate=framerate, **kwargs)
        elif (use_camera == CameraEnum.OPENCV) or (use_camera == CameraEnum.AUTO and machine in ('aarch64')):
            self.stream = CameraOpenCV(src=src, resolution=resolution, framerate=framerate)
        elif use_camera in (CameraEnum.FILE, CameraEnum.AUTO):
            self.stream = CameraFile()

    def update(self, event: Event) -> None:
        """update to next picture on thread event"""
        self.stream.update(event)

    def read(self, peek=False) -> Mat:
        """read next picture (no counter increment if peek=True when using CameraFile)"""
        from .camera_file import CameraFile
        if isinstance(self.stream, CameraFile):
            return self.stream.read(peek=peek)
        return self.stream.read()

    def cancel(self) -> None:
        """end of video thread"""
        self.stream.cancel()

    def done(self, result: Future) -> None:
        """signal end of video thread"""
        self.stream.done(result)
