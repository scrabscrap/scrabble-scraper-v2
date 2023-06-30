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
import logging
import os.path
from threading import Event
from typing import Optional

import cv2
import numpy as np

from config import Config

Mat = np.ndarray[int, np.dtype[np.generic]]

_resolution = (Config.video_width(), Config.video_height())
formatter: str = Config.simulate_path()
cnt: int = 1


def init(new_formatter: Optional[str] = None, resolution=(Config.video_width(), Config.video_height())):
    """init/config cam"""
    global _resolution, formatter  # pylint: disable=global-statement
    logging.info('### init MockCamera')
    _resolution = resolution
    if new_formatter is not None:
        formatter = new_formatter
    else:
        formatter = Config.simulate_path()


def read(peek=False) -> Mat:
    """read next picture (no counter increment if peek=True)"""
    global cnt  # pylint: disable=global-statement
    logging.debug(f"read {cnt}: {formatter.format(cnt)} with peek={peek}")
    img = cv2.imread(formatter.format(cnt))
    if not peek:
        cnt += 1 if os.path.isfile(formatter.format(cnt + 1)) else 0
    return cv2.resize(img, _resolution)


def update(event: Event) -> None:
    """update to next picture on thread event"""
    while event.wait(0.05):
        pass
    event.clear()
