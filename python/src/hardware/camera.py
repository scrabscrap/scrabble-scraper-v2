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

from config import config
from util import TImage, runtime_measure

camera_dict: dict = {}
logging.basicConfig(level=logging.INFO, force=True)


class Camera(Protocol):
    """Camera Protocol"""

    def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
        """constructor"""

    def read(self, peek: bool = False) -> TImage:
        """read next picture"""

    def update(self, event: Event) -> None:
        """update to next picture on thread event"""

    def cancel(self) -> None:
        """end of video thread"""


if importlib.util.find_spec('picamera'):
    import subprocess

    from picamera import PiCamera  # type: ignore # pylint: disable=import-error
    from picamera.array import PiRGBArray  # type: ignore # pylint: disable=import-error

    class CameraRPIStill(Camera):  # pylint: disable=too-many-instance-attributes
        """uses RPI camera no continuous_capture"""

        def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
            self.resolution = resolution if resolution else (config.video_width, config.video_height)
            self.framerate = framerate if framerate else config.video_fps
            self.frame = np.empty((self.resolution[0] * self.resolution[1] * 3,), dtype=np.uint8)
            self.lastframe = np.array([])
            self.camera = PiCamera(sensor_mode=4, resolution=self.resolution, framerate=self.framerate)
            logging.info(f'open camera: {self.camera.resolution} / {self.camera.framerate} / {self.camera.sensor_mode}')
            if config.video_rotate:
                self.camera.rotation = 180
            sleep(2)
            while self.camera.analog_gain < 0:
                sleep(0.1)
            atexit.register(self._atexit)                                                       # cleanup on exit

        def _atexit(self) -> None:
            logging.error('close camera')
            if self.camera:
                self.camera.close()
            self.frame = np.array([])

        @runtime_measure
        def read(self, peek: bool = False) -> TImage:
            if np.array_equal(self.lastframe, self.frame):
                logging.warning('image is equal to previous image')
            self.lastframe = self.frame.copy()
            self.camera.capture(self.frame, 'bgr')
            self.frame = self.frame.reshape((self.resolution[1], self.resolution[0], 3))
            return self.frame

        def update(self, event: Event) -> None:
            pass

        def cancel(self) -> None:
            self._atexit()

    class CameraRPI(Camera):  # pylint: disable=too-many-instance-attributes
        """uses RPI camera with continuous_capture"""

        def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
            self.resolution = resolution if resolution else (config.video_width, config.video_height)
            self.framerate = framerate if framerate else config.video_fps
            self.frame = np.array([])
            self.lastframe = np.array([])
            self.event: Optional[Event] = None
            self.camera = PiCamera(sensor_mode=4, resolution=self.resolution, framerate=self.framerate)
            if config.video_rotate:
                self.camera.rotation = 180
            self.raw_capture = PiRGBArray(self.camera, size=self.camera.resolution)
            sleep(2)  # warm up camera
            while self.camera.analog_gain < 0:
                sleep(0.1)
            self.stream = self.camera.capture_continuous(self.raw_capture, format="bgr", use_video_port=True)
            logging.debug(f'open camera: {self.camera.resolution} / {self.camera.framerate} / {self.camera.sensor_mode}')
            atexit.register(self._atexit)                                                       # cleanup on exit

        def _camera_close(self) -> None:
            if self.stream:
                self.stream.close()
            if self.camera:
                self.camera.close()

        def _atexit(self) -> None:
            logging.error('close camera')
            self._camera_close()
            self.frame = np.array([])

        def read(self, peek: bool = False) -> TImage:
            if np.array_equal(self.lastframe, self.frame):
                logging.warning('image is equal to previous image')
            self.lastframe = self.frame
            return self.frame

        def update(self, event: Event) -> None:
            self.event = event
            for images in self.stream:
                self.frame = images.array
                self.raw_capture.truncate(0)
                if event.is_set():
                    logging.info('event is set - exit update cam')
                    break
                sleep(0.04)  # approx 25 fps
            self._atexit()
            event.clear()

        def cancel(self) -> None:
            if self.event:
                self.event.set()
            else:
                self._atexit()

    process = subprocess.run(['vcgencmd', 'get_camera'], check=False, capture_output=True)
    if 'detected=1' in process.stdout.decode():
        camera_dict.update({'picamera': CameraRPI})
        camera_dict.update({'picamera-still': CameraRPIStill})
        logging.info('picamera added')
    else:
        logging.error(f'picamera not detected {process.stdout.decode()}')

elif importlib.util.find_spec('picamera2'):
    import subprocess

    import libcamera  # type: ignore # pylint: disable=import-error
    from picamera2 import Picamera2  # type: ignore # pylint: disable=import-error

    class CameraRPI64(Camera):
        """uses RPI 64bit camera"""

        def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
            """init/config cam"""

            logging.info('### init PiCamera 64')
            self.resolution = resolution if resolution else (config.video_width, config.video_height)
            self.framerate = framerate if framerate else config.video_fps
            self.frame = np.array([])
            self.lastframe = np.array([])
            self.event: Optional[Event] = None
            self.camera = Picamera2()
            cfg = self.camera.create_still_configuration(main={"format": 'XRGB8888', "size": resolution})
            if config.video_rotate:
                cfg["transform"] = libcamera.Transform(hflip=1, vflip=1)  # self.camera.rotation = 180
            self.camera.configure(cfg)
            self.camera.start()
            self.wait = round(1 / framerate, 2)  # type: ignore
            sleep(1.5)  # warmup camera
            atexit.register(self._atexit)

        def _atexit(self) -> None:
            logging.debug('rpi 64: camera close')
            if self.camera is not None:
                self.camera.close()

        def read(self, peek: bool = False) -> TImage:
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

    process = subprocess.run(['vcgencmd', 'get_camera'], check=False, capture_output=True)
    if 'detected=1' in process.stdout.decode():
        camera_dict.update({'picamera': CameraRPI64})
        camera_dict.update({'picamera2': CameraRPI64})
        logging.info('picamera2 added')
    else:
        logging.error(f'picamera2 not detected {process.stdout.decode()}')


class CameraFile(Camera):
    """Implementation for file access"""

    def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
        self.resolution = resolution if resolution else (config.video_width, config.video_height)
        self.framerate = framerate if framerate else config.video_fps
        self._counter = 1
        self._formatter = config.simulate_path
        self._resize = True
        self.last_img = np.array([])

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
    def read(self, peek: bool = False) -> TImage:
        logging.debug(f'CameraFile read: {self._formatter.format(self._counter)}')
        img = cv2.imread(self._formatter.format(self._counter))
        if not peek:
            self._counter += 1 if os.path.isfile(self._formatter.format(self._counter + 1)) else 0
        if self._resize:
            img = cv2.resize(img, self.resolution)
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
        self.resolution = resolution if resolution else (config.video_width, config.video_height)
        self.framerate = framerate if framerate else config.video_fps
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
        sleep(1.5)                                                                          # warm up camera
        atexit.register(self._atexit)                                                       # cleanup on exit

    def _atexit(self) -> None:
        self.stream.release()
        self.frame = np.array([])

    def read(self, peek: bool = False) -> TImage:
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
            sleep(0.04)  # approx 25 fps
        event.clear()
        self._atexit()

    def cancel(self) -> None:
        if self.event:
            self.event.set()
        else:
            self._atexit()


camera_dict.update({
    "file": CameraFile,
    "opencv": CameraOpenCV
})


# default picamera - fallback file
cam: Camera = camera_dict['picamera-still']() if 'picamera-still' in camera_dict else camera_dict['file']()


def switch_camera(camera: str) -> Camera:
    """switch camera - threadpool has to be restarted"""
    global cam  # pylint: disable=global-statement

    if camera == '':
        if cam:
            clazz = cam.__class__
            cam.cancel()
            sleep(1)
            logging.info('restart camera')
            cam = clazz()
    elif camera.lower() in camera_dict:
        if cam:
            cam.cancel()
        logging.info(f'switch camera to {camera}')
        cam = camera_dict[camera]()
    else:
        raise ValueError(f'invalid camera selected: {camera}')
    return cam


def main() -> None:
    """main function"""
    import sys

    from threadpool import pool

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, force=True,
                        format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')

    logging.info(f'>> config {camera_dict}')
    switch_camera('file')
    logging.info(f'cam type: {type(cam)}')
    pool.submit(cam.update, event=Event())                                                  # start cam
    sleep(5)
    switch_camera('opencv')
    logging.info(f'cam type: {type(cam)}')
    pool.submit(cam.update, event=Event())                                                  # start cam
    sleep(5)
    switch_camera('')
    logging.info(f'cam type: {type(cam)}')
    pool.submit(cam.update, event=Event())                                                  # restart cam
    sleep(5)
    try:
        switch_camera('picamera')
        logging.info(f'cam type: {type(cam)}')
        pool.submit(cam.update, event=Event())                                              # start cam
        sleep(5)
    except ValueError as oops:
        logging.error(f'{oops}')
    cam.cancel()


if __name__ == '__main__':
    main()
