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
import logging
import logging.config
import os
import signal
from threading import Event
from time import sleep

import cv2
from vlogging import VisualRecord

logging.config.fileConfig(fname=os.path.dirname(os.path.abspath(__file__)) + '/../work/log.conf',
                          disable_existing_loggers=False,
                          defaults={'level': 'DEBUG',
                                    'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})
visualLogger = logging.getLogger("visualLogger")

from custom import Custom
from hardware.camera import Camera
from processing import analyze, filter_candidates, filter_image
from threadpool import pool
from util import rotate_logs


def main() -> None:

    def main_cleanup(signum, frame) -> None:
        logging.debug(f'Signal handler called with signal {signum}')
        cam_future.cancel()
        cam_event.set()
        # reset alarm
        signal.alarm(0)

    signal.signal(signal.SIGALRM, main_cleanup)

    rotate_logs('visualLogger')

    # open Camera
    cam = Camera()
    # cam = MockCamera()
    cam_event = Event()
    cam_future = pool.submit(cam.update, cam_event)
    sleep(1)  # camera warmup

    img = cam.read()
    # _, img = cv2.imencode(".jpg", img)
    visualLogger.info(VisualRecord("Camera", [img], fmt="png"))
    # cv2.imwrite('log/img.jpg', img)

    warped = Custom.warp(img)
    visualLogger.info(VisualRecord("Warped", [warped], fmt="png"))
    # cv2.imwrite('log/warped.jpg', warped)

    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)                     # grayscale image
    visualLogger.info(VisualRecord("Warped-Gray", [warped_gray], fmt="png"))
    # cv2.imwrite('log/warped_gray.jpg', warped_gray)

    filtered, tiles_candidates = filter_image(warped)                          # find potential tiles on board
    ignore_coords = set()  # only analyze tiles from last 3 moves
    filtered_candidates = filter_candidates((7, 7), tiles_candidates.copy(), ignore_coords)

    logging.debug(f'filtered candidated: {filtered_candidates}')

    # previous board information
    board = {}
    # previous_board = board.copy()
    # previous_score = (0, 0)

    # picture analysis
    analyze(warped_gray, board, filtered_candidates)

    logging.debug(f'board: {board}')
    cam_future.cancel()
    cam_event.set()


if __name__ == '__main__':
    main()
