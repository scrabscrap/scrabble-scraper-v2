"""Tryout Camera"""
import atexit
import logging
import os
import sys
from threading import Event
from time import sleep
from typing import Optional, Protocol

import cv2
import numpy as np

from config import Config

Mat = np.ndarray[int, np.dtype[np.generic]]


class Camera(Protocol):
    """Implementation of camera threads"""

    def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
        """constructor"""

    def read(self, peek: bool = False) -> Mat:
        """read next picture"""

    def update(self, event: Event) -> None:
        """update to next picture on thread event"""

    def cancel(self) -> None:
        """end of video thread"""


class CameraFile(Camera):
    """Implementation for file access"""

    def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
        self.resolution = resolution if resolution else (Config.video_width(), Config.video_height())
        self.framerate = framerate if framerate else Config.video_fps()
        self._counter = 1
        self._formatter = Config.simulate_path()
        self._resize = True

    @property
    def resize(self) -> bool:
        """resize image true/false"""
        return self._resize

    @resize.setter
    def resize(self, value: bool) -> None:
        self._resize = value

    @property
    def formatter(self) -> str:
        """attribute formatter for reading image files"""
        return self._formatter

    @formatter.setter
    def formatter(self, value: str) -> None:
        self._formatter = value

    @property
    def counter(self) -> int:
        """current counter of image file"""
        return self._counter

    @counter.setter
    def counter(self, value: int) -> None:
        self._counter = value

    def read(self, peek: bool = False) -> Mat:
        img = cv2.imread(self._formatter.format(self._counter))
        if not peek:
            self._counter += 1 if os.path.isfile(self._formatter.format(self._counter + 1)) else 0
        if self._resize:
            return cv2.resize(img, self.resolution)
        return img

    def update(self, event: Event) -> None:
        while event.wait(0.05):
            pass
        event.clear()

    def cancel(self) -> None:
        self._counter = 1


class CameraOpenCV(Camera):
    """camera implementation for OpenCV"""

    def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
        self.resolution = resolution if resolution else (Config.video_width(), Config.video_height())
        self.framerate = framerate if framerate else Config.video_fps()
        # self.stream = cv2.VideoCapture(f'/dev/video{src}', cv2.CAP_V4L)
        self.stream = cv2.VideoCapture(0)
        if not self.stream.isOpened():
            logging.error('CameraOpenCV can not open camera')
            sys.exit(-1)
        else:
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.stream.set(cv2.CAP_PROP_FPS, self.framerate)
        self.frame = np.array([])
        self.event: Optional[Event] = None
        sleep(1)                                                                            # warm up camera
        atexit.register(self._atexit)                                                       # cleanup on exit

    def _atexit(self) -> None:
        self.stream.release()
        self.frame = np.array([])

    def read(self, peek: bool = False) -> Mat:
        return self.frame

    def update(self, event: Event) -> None:
        self.event = event
        while True:
            valid, self.frame = self.stream.read()  # type: ignore
            if not valid:
                logging.warning('CameraOpenCV: frame not valid')
            if Config.video_rotate():
                self.frame = cv2.rotate(self.frame, cv2.ROTATE_180)
            if event.is_set():
                break
            sleep(0.04)  # approx 25 fps
        event.clear()
        self._atexit()
        return super().update(event)

    def cancel(self) -> None:
        if self.event:
            self.event.set()
        else:
            self._atexit()


camera_dict: dict = {
    "file": CameraFile,
    "opencv": CameraOpenCV
}
