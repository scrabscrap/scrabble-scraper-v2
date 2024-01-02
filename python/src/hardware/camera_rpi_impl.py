"""rpi cam"""
import atexit
import importlib.util
import logging
import subprocess
from threading import Event
from time import sleep
from typing import Optional

import numpy as np

from config import config
from hardware.camera_impl import Camera, camera_dict

try:
    from picamera import PiCamera, PiCameraError  # type: ignore
    from picamera.array import PiRGBArray  # type: ignore
    RPI_CAMERA = True
except ImportError:
    logging.error('>>> no PICamera available <<<')
    from hardware.fake_picamera import (  # pylint: disable=ungrouped-imports
        PiCamera, PiRGBArray)
    RPI_CAMERA = False

Mat = np.ndarray[int, np.dtype[np.generic]]


class CameraRPI(Camera):  # pylint: disable=too-many-instance-attributes
    """uses RPI camera"""

    def __init__(self, src: int = 0, resolution: Optional[tuple[int, int]] = None, framerate: Optional[int] = None):
        self.resolution = resolution if resolution else (config.video_width, config.video_height)
        self.framerate = framerate if framerate else config.video_fps
        self.frame = np.array([])
        self.lastframe = np.array([])
        self.frame_index = -1
        self.event: Optional[Event] = None
        self._camera_open()
        atexit.register(self._atexit)                                                       # cleanup on exit

    def _camera_open(self) -> None:
        global RPI_CAMERA  # pylint: disable=global-statement

        try:
            self.camera = PiCamera(sensor_mode=4, resolution=self.resolution, framerate=self.framerate)
        except PiCameraError as oops:
            logging.error(f'camera error {oops}')
            RPI_CAMERA = False
            del camera_dict['picamera']
            return
        if config.video_rotate:
            self.camera.rotation = 180
        self.raw_capture = PiRGBArray(self.camera, size=self.camera.resolution)
        sleep(0.3)  # warm up camera
        self.stream = self.camera.capture_continuous(self.raw_capture, format="bgr", use_video_port=True)
        logging.debug(f'open camera: {self.camera.resolution} / {self.camera.framerate} / {self.camera.sensor_mode}')

    def _camera_close(self) -> None:
        if self.stream:
            self.stream.close()
        if self.camera:
            self.camera.close()

    def _atexit(self) -> None:
        logging.error('rpi: camera close')
        self._camera_close()
        self.frame = np.array([])

    def read(self, peek: bool = False) -> Mat:
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


# add 'picamera' to camera dict if 'picamera' is available
if importlib.util.find_spec('picamera'):
    process = subprocess.run(['vcgencmd', 'get_camera'], check=False, capture_output=True)
    if 'detected=1' in process.stdout.decode():
        camera_dict.update({'picamera': CameraRPI})
        logging.info('picamera added')
    else:
        RPI_CAMERA = False
        logging.error(f'picamera not detected {process.stdout.decode()}')
