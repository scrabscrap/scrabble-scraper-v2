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
import signal
from threading import Event
from time import sleep
from concurrent import futures

import cv2
from vlogging import VisualRecord

from config import config

logging.config.fileConfig(fname=config.WORK_DIR + '/log.conf', disable_existing_loggers=False,
                          defaults={'level': 'DEBUG',
                                    'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})

from custom import Custom
from hardware.camera import Camera
from processing import analyze, filter_candidates, filter_image
from threadpool import pool
from util import rotate_logs
from game_board.board import overlay_grid, overlay_tiles

rotate_logs('visualLogger')
visualLogger = logging.getLogger("visualLogger")


def print_board(board: dict) -> str:
    result = '  |'
    for i in range(15):
        result += f'{(i + 1):2d} '
    result += ' | '
    for i in range(15):
        result += f'{(i + 1):2d} '
    result += '\n'
    for row in range(15):
        result += f"{chr(ord('A') + row)} |"
        for col in range(15):
            if (col, row) in board:
                result += f' {board[(col, row)][0]} '
            else:
                result += ' . '
        result += ' | '
        for col in range(15):
            result += f' {str(board[(col, row)][1])}' if (col, row) in board else ' . '
        result += ' | \n'
    return result


def main() -> None:

    def main_cleanup(signum, frame) -> None:
        logging.debug(f'Signal handler called with signal {signum}')
        cam_future.cancel()
        cam_event.set()
        # reset alarm
        signal.alarm(0)

    def chunkify(lst, n):
        return [lst[i::n] for i in range(n)]

    signal.signal(signal.SIGALRM, main_cleanup)

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
    logging.debug(f'tiles candidated: {tiles_candidates}')
    ignore_coords = set()  # only analyze tiles from last 3 moves
    filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
    logging.debug(f'filtered candidated: {filtered_candidates}')

    # previous board information
    board = {}
    # previous_board = board.copy()
    # previous_score = (0, 0)

    # picture analysis
    # analyze(warped_gray, board, filtered_candidates)
    chunks = chunkify(list(filtered_candidates), 3)
    future1 = pool.submit(analyze, warped_gray, board, set(chunks[0]))  # 1. thread
    future2 = pool.submit(analyze, warped_gray, board, set(chunks[1]))  # 2. thread
    analyze(warped_gray, board, set(chunks[2]))                         # 3. (this) thread
    done, _ = futures.wait({future1, future2})                          # blocking wait
    assert len(done) == 2, 'error on wait to futures'

    logging.debug(f'board: \n{print_board(board)}')

    overlay = overlay_grid(warped)
    overlay = overlay_tiles(overlay, board)
    visualLogger.info(VisualRecord("Overlayed", [overlay], fmt="png"))

    cam_future.cancel()
    cam_event.set()


if __name__ == '__main__':
    main()
