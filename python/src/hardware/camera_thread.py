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
from enum import Enum
from threading import Event
from typing import Optional

import numpy as np

import hardware.camera_file as cam_file
import hardware.camera_opencv as cam_opencv
import hardware.camera_rpi as cam_rpi
from config import Config
from util import trace

Mat = np.ndarray[int, np.dtype[np.generic]]


class CameraEnum(Enum):
    """Enumation of supported camera types"""
    AUTO = 1
    PICAMERA = 2
    OPENCV = 3
    FILE = 4


_camera: CameraEnum = CameraEnum.PICAMERA
_resolution: tuple[int, int] = (Config.video_width(), Config.video_height())
_framerate: int = Config.video_fps()
_is_init: bool = False
_event: Optional[Event] = None


@trace
def init(src: int = 0, use_camera: CameraEnum = _camera,  # pylint: disable=unused-argument
         resolution=_resolution, framerate=_framerate):
    """init/config cam"""
    global _is_init, _camera, _resolution, _framerate  # pylint: disable=global-statement
    _camera = use_camera
    _resolution = resolution
    _framerate = framerate
    if use_camera == CameraEnum.PICAMERA:
        cam_rpi.init(resolution=resolution, framerate=framerate)
    elif use_camera == CameraEnum.FILE:
        cam_file.init(new_formatter=None, resolution=resolution)
    elif use_camera == CameraEnum.OPENCV:
        cam_opencv.init(src=src, resolution=resolution, framerate=framerate)
    else:
        cam_file.init(new_formatter=None, resolution=resolution)
        _camera = CameraEnum.FILE
    _is_init = True


def switch_cam(cam: CameraEnum) -> None:
    """select new cam"""
    global _camera  # pylint: disable=global-statement
    if cam != _camera:
        cancel()
    _camera = cam
    init()


@trace
def update(event: Event) -> None:
    """update to next picture on thread event"""
    global _event  # pylint: disable=global-statement
    if not _is_init:
        init()
    _event = event
    if _camera == CameraEnum.PICAMERA:
        cam_rpi.update(event)
    elif _camera == CameraEnum.FILE:
        cam_file.update(event)
    elif _camera == CameraEnum.OPENCV:
        cam_opencv.update(event)
    else:
        cam_file.update(event)


@trace
def read(peek=False) -> Mat:
    """read next picture (no counter increment if peek=True when using CameraFile)"""
    if _camera == CameraEnum.PICAMERA:
        return cam_rpi.read()
    if _camera == CameraEnum.FILE:
        return cam_file.read(peek=peek)
    if _camera == CameraEnum.OPENCV:
        return cam_opencv.read()
    return cam_file.read()


@trace
def cancel() -> None:
    """end of video thread"""
    if _event is not None:
        _event.set()
