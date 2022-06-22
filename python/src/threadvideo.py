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
import atexit
import time
from threading import Thread

from config import config
from mock import mockvideo

try:
    # noinspection PyUnresolvedReferences
    from picamera import PiCamera  # type: ignore
    # noinspection PyUnresolvedReferences
    from picamera.array import PiRGBArray  # type: ignore
    NO_CAM = False
except ImportError:
    NO_CAM = True


class VideoThread:

    def __init__(self, width=config.IM_WIDTH, height=config.IM_HEIGHT, fps=config.FPS):
        self.name = 'VideoThread'
        self.stopped = False
        resolution = (width, height)
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = fps
        if config.ROTATE:
            self.camera.rotation = 180
        self.rawCapture = PiRGBArray(self.camera, (972, 972))
        self.stream = self.camera.capture_continuous(self.rawCapture, format="bgr",
                                                     use_video_port=True, resize=(972, 972))
        atexit.register(self.stop)
        time.sleep(2)  # wait for awb
        self.frame = []

    def start(self):
        # start the thread
        thread = Thread(target=self.update, name=self.name, args=())
        thread.daemon = True
        thread.start()
        return self

    def stop(self):
        self.stopped = True

    def read(self):
        return self.frame

    # def picture(self):
    #     _capture = PiRGBArray(self.camera, size=(IM_WIDTH, IM_HEIGHT))
    #     self.camera.capture(_capture, format="bgr")
    #     return _capture.array

    def update(self):
        for file in self.stream:
            # todo: caching of pictures to find a picture without movement
            self.frame = file.array
            # self.rawCapture.seek(0)
            self.rawCapture.truncate(0)
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()


if config.SIMULATE or NO_CAM:
    video_thread = mockvideo.VideoSimulate(formatter=config.SIMULATE_PATH)
else:
    video_thread = VideoThread()
