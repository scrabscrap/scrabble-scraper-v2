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
import logging.config
import signal
from concurrent import futures
from threading import Event
from time import sleep

import cv2

from config import Config

logging.config.fileConfig(fname=Config.work_dir() + '/log.conf', disable_existing_loggers=False,
                          defaults={'level': 'DEBUG',
                                    'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})

from game_board.board import overlay_grid, overlay_tiles
from hardware.camera_thread import Camera
from processing import analyze, filter_candidates, filter_image, warp_image
from threadpool import pool


def print_board(board: dict) -> str:
    """print out scrabble board dictionary"""
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
    """main entry for starting"""

    def main_cleanup(signum, _) -> None:
        logging.debug(f'Signal handler called with signal {signum}')
        cam.cancel()
        # reset alarm
        signal.alarm(0)

    def chunkify(lst, chunks):
        return [lst[i::chunks] for i in range(chunks)]

    signal.signal(signal.SIGALRM, main_cleanup)

    # open Camera
    cam = Camera()
    # cam = MockCamera()
    _ = pool.submit(cam.update, Event())
    sleep(1)  # camera warmup

    img = cam.read()
    # _, img = cv2.imencode(".jpg", img)
    cv2.imwrite('log/img.jpg', img)

    warped, warped_gray = warp_image(img)
    cv2.imwrite('log/warped.jpg', warped)
    cv2.imwrite('log/warped_gray.jpg', warped_gray)

    _, tiles_candidates = filter_image(warped)                          # find potential tiles on board
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
    cv2.imwrite('log/overlay.jpg', overlay)

    cam.cancel()
    pool.shutdown(cancel_futures=True)


if __name__ == '__main__':
    main()
