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
import importlib.util
import logging
import os
from threading import Event
from time import sleep
from typing import Optional, Protocol

import cv2
import numpy as np
from cv2.typing import MatLike

from config import config
from util import runtime_measure

camera_dict: dict = {}
logging.basicConfig(filename=f'{config.work_dir}/log/messages.log', level=logging.INFO, force=True)


class Camera(Protocol):
    """Camera Protocol"""

    def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
        """constructor"""

    def read(self, peek: bool = False) -> MatLike:  # type: ignore
        """read next picture"""

    def update(self, event: Event) -> None:
        """update to next picture on thread event"""

    def cancel(self) -> None:
        """end of video thread"""

    def log_camera_info(self) -> None:
        """log camera infos with level=info"""


if importlib.util.find_spec('picamera2'):
    import libcamera  # type: ignore # pylint: disable=import-error
    from picamera2 import Picamera2  # type: ignore # pylint: disable=import-error

    class CameraRPI64(Camera):
        """uses RPI 64bit camera"""

        def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
            """init/config cam"""
            logging.info('### init CameraRPI64')
            self.resolution = resolution or (config.video_width, config.video_height)
            self.framerate = framerate or config.video_fps
            self.frame = np.zeros(shape=(self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
            self.event: Optional[Event] = None
            self.camera = Picamera2()
            logging.info(f'open CameraRPI64: {self.resolution=} {self.framerate=}')
            cfg = self.camera.create_still_configuration(main={'format': 'RGB888', 'size': self.resolution})
            if config.video_rotate:
                cfg['transform'] = libcamera.Transform(hflip=1, vflip=1)  # self.camera.rotation = 180
            self.camera.configure(cfg)
            self.camera.start()
            self.wait = round(1 / self.framerate, 2)  # type: ignore
            sleep(2)  # warmup camera
            self.frame = self.camera.capture_array()
            atexit.register(self._atexit)

        def log_camera_info(self) -> None:
            logging.info('using camera CameraRPI64')
            logging.info(f'{self.resolution=} {self.framerate=}')
            logging.info(f'{self.camera.camera_configuration()}')

        def _atexit(self) -> None:
            logging.debug('rpi 64: camera close')
            atexit.unregister(self._atexit)
            if self.camera is not None:
                self.camera.close()

        @runtime_measure
        def read(self, peek: bool = False) -> MatLike:
            """read next picture"""
            return self.frame

        def update(self, event: Event) -> None:
            """update to next picture on thread event"""
            self.event = event
            while True:
                self.frame = self.camera.capture_array()  # type: ignore
                if event.is_set():
                    break
                sleep(self.wait)
            event.clear()
            self._atexit()

        def cancel(self) -> None:
            if self.event:
                self.event.set()
                sleep(2 * self.wait)
            else:
                self._atexit()

    if Picamera2.global_camera_info():
        camera_dict.update({'picamera': CameraRPI64})
        camera_dict.update({'picamera2': CameraRPI64})
        camera_dict.update({'picamera-still': CameraRPI64})
        logging.info('picamera2 added')
    else:
        logging.error('picamera2 not detected')


class CameraFile(Camera):
    """Implementation for file access"""

    def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
        logging.info('### init CameraFile')
        self.resolution = resolution or (config.video_width, config.video_height)
        self.framerate = framerate or config.video_fps
        self._counter = 1
        self._formatter = config.simulate_path
        self._resize = True
        self.frame = np.zeros(shape=(self.resolution[1], self.resolution[0], 3), dtype=np.uint8)

    def log_camera_info(self) -> None:
        logging.info('using camera CameraFile')
        logging.info(f'{self.resolution=} {self.framerate=}')
        logging.info(f'{self._counter=} {self._formatter=}')

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

    @runtime_measure
    def read(self, peek: bool = False) -> MatLike:
        logging.debug(f'CameraFile read: {self._formatter.format(self._counter)}')
        img = cv2.imread(self._formatter.format(self._counter))
        if not peek:
            self._counter += 1 if os.path.isfile(self._formatter.format(self._counter + 1)) else 0
        if img is not None and self._resize:
            img = cv2.resize(img, self.resolution)
        return img

    def update(self, event: Event) -> None:
        pass

    def cancel(self) -> None:
        self._counter = 1


class CameraOpenCV(Camera):
    """camera implementation for OpenCV"""

    def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
        logging.info('### init CameraOpenCV')
        self.resolution = resolution or (config.video_width, config.video_height)
        self.framerate = framerate or config.video_fps
        self.wait = round(1 / self.framerate, 2)  # type: ignore
        # self.stream = cv2.VideoCapture(f'/dev/video{src}', cv2.CAP_V4L)
        self.stream = cv2.VideoCapture(0)  # type: ignore # mypy: Too many arguments for "VideoCapture"
        if not self.stream.isOpened():
            logging.error('CameraOpenCV can not open camera')
        else:
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.stream.set(cv2.CAP_PROP_FPS, self.framerate)
        self.frame = np.array([])
        self.event: Optional[Event] = None
        sleep(2)  # warm up camera
        atexit.register(self._atexit)  # cleanup on exit

    def log_camera_info(self) -> None:
        logging.info('using camera CameraOpenCV')
        logging.info(f'{self.resolution=} {self.framerate=}')

    def _atexit(self) -> None:
        atexit.unregister(self._atexit)
        self.stream.release()
        self.frame = np.array([])

    @runtime_measure
    def read(self, peek: bool = False) -> MatLike:
        return self.frame

    def update(self, event: Event) -> None:
        self.event = event
        while True:
            valid, self.frame = self.stream.read()  # type: ignore
            if not valid:
                logging.warning('CameraOpenCV: frame not valid')
            if config.video_rotate:
                self.frame = cv2.rotate(self.frame, cv2.ROTATE_180)
            if event.is_set():
                break
            sleep(self.wait)
        event.clear()
        self._atexit()

    def cancel(self) -> None:
        if self.event:
            self.event.set()
            sleep(2 * self.wait)
        else:
            self._atexit()


camera_dict.update({'file': CameraFile, 'opencv': CameraOpenCV})


# default picamera - fallback file
cam: Camera = (
    camera_dict['picamera-still']() if not config.is_testing and 'picamera-still' in camera_dict else camera_dict['file']()
)


def switch_camera(camera: str) -> Camera:
    """switch camera - restarts threadpool thread for camera"""
    global cam  # pylint: disable=global-statement
    from threadpool import pool

    if not camera and cam:
        logging.info('restart camera')
        clazz = cam.__class__
    elif camera.lower() in camera_dict:
        logging.info(f'switch camera to {camera}')
        clazz = camera_dict[camera]
    else:
        logging.error(f'invalid camera selected: {camera}')
        raise ValueError(f'invalid camera selected: {camera}')

    if cam:
        cam.cancel()

    if clazz.__name__ != 'CameraFile':
        sleep(1)
        cam = clazz()
        pool.submit(cam.update, event=Event())  # start cam
    cam.log_camera_info()
    return cam


# test and debug
def main() -> None:
    """main function"""
    import sys

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        force=True,
        format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s',
    )

    logging.info(f'>> config {camera_dict}')
    switch_camera('file')
    logging.info(f'cam type: {type(cam)}')
    cam.log_camera_info()
    sleep(5)

    switch_camera('opencv')
    logging.info(f'cam type: {type(cam)}')
    cam.log_camera_info()
    sleep(5)

    switch_camera('')
    logging.info(f'cam type: {type(cam)}')
    sleep(5)
    cam.log_camera_info()

    try:
        switch_camera('picamera')
        logging.info(f'cam type: {type(cam)}')
        cam.log_camera_info()
        sleep(5)
    except ValueError as oops:
        logging.error(f'{oops}')
    cam.cancel()


if __name__ == '__main__':
    main()
