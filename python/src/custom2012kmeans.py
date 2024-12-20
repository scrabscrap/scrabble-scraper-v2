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
from concurrent import futures
from itertools import product
from typing import Optional

import cv2
import numpy as np
from cv2.typing import MatLike

from config import config
from customboard import CustomBoard
from game_board.board import DOUBLE_LETTER, DOUBLE_WORDS, GRID_H, GRID_W, OFFSET, TRIPLE_LETTER, TRIPLE_WORDS
from threadpool import pool

# dimension board custom
# ----------------------
# overall size: 330mm x 330mm
# grid: 310mm x 310mm
# top: 10mm
# left: 10mm
# right: 10mm
# bottom: 10mm
#
# tiles
# -----
# 19mm x 19mm

# pylint: disable=duplicate-code


class Custom2012kBoard(CustomBoard):
    """Implementation custom scrabble board analysis"""

    # defaults: custom board 2012
    FIELD_COLOR = ([30, 85, 10], [90, 255, 255])

    TLETTER_COLOR = ([95, 60, 10], [130, 255, 255])
    DLETTER_COLOR = ([95, 60, 10], [130, 255, 255])

    TWORD_COLOR = ([145, 100, 10], [190, 255, 255])  # H: 0-10 & 145-180
    DWORD_COLOR = ([145, 100, 10], [190, 255, 255])  # H: 0-10 & 145-180

    last_warp = None

    @classmethod
    def log_color_table(cls, color_table, candidates) -> str:
        """print color table"""
        board_size = 15
        tmp = ''
        for color in range(3):
            tmp += '  |' + ''.join(f'  {i + 1:-3d} ' for i in range(board_size)) + '\n'
            tmp += '\n'.join(
                [
                    f"""{chr(ord('A') + row)} |{''.join(f' [{color_table[(col, row)][color]:-3d}]' if (col, row) in candidates
                                 else f'  {color_table[(col, row)][color]:-3d} ' for col in range(board_size))}|"""
                    for row in range(board_size)
                ]
            )
            tmp += '\n\n'
        return tmp

    @classmethod
    def filter_image(cls, _image: MatLike) -> tuple[Optional[MatLike], set]:
        # pylint: disable=too-many-statements,too-many-locals
        """implement filter for custom board"""

        def between(val: tuple[int, int, int], lower: list[int], upper: list[int]) -> bool:
            """check if hsl value is between lower and upper"""
            if upper[0] > 180:
                return (
                    (lower[0] <= val[0] or val[0] <= (upper[0] - 180))
                    and (lower[1] <= val[1] <= upper[1])
                    and (lower[2] <= val[2] <= upper[2])
                )
            return all(lower[i] <= val[i] <= upper[i] for i in range(3))

        def is_tile(coord: tuple[int, int], color: tuple[int, int, int]) -> bool:
            if coord in TRIPLE_WORDS:  # dark red
                return not between(color, *cls.TWORD_COLOR)
            if coord in DOUBLE_WORDS:  # light red
                return not between(color, *cls.TWORD_COLOR)
            if coord in TRIPLE_LETTER:  # dark blue
                return not between(color, *cls.TLETTER_COLOR)
            if coord in DOUBLE_LETTER:  # light blue
                return not between(color, *cls.DLETTER_COLOR)
            # green
            return not between(color, *cls.FIELD_COLOR)

        def filter_set_of_positions(coord: set, img: MatLike, result: MatLike, color_table: dict, set_of_tiles: set) -> dict:
            # pylint: disable=too-many-locals, disable=too-many-arguments
            offset = int(OFFSET / 2)  # use 400x400 instead of 800x800
            grid_h = int(GRID_H / 2)
            grid_w = int(GRID_W / 2)
            for col, row in coord:
                px_col = int(offset + (row * grid_h))
                px_row = int(offset + (col * grid_w))
                segment = img[px_col + 2 : px_col + grid_h - 2, px_row + 2 : px_row + grid_w - 2]
                info = img[px_col + 1 : px_col + grid_h - 1, px_row + 1 : px_row + grid_w - 1]
                # segment[:, :, 2] = 255  # ignore value for kmeas
                data = segment.reshape((-1, 3))
                data = np.float32(data)  # type: ignore

                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 8, 1.0)
                k = 3
                _, label, center = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)  # type: ignore[call-overload] # noqa: E501 # pylint: disable=line-too-long
                reduced = np.uint8(center)[label.flatten()]  # type: ignore # pylint: disable=unsubscriptable-object
                unique, counts = np.unique(reduced.reshape(-1, 3), axis=0, return_counts=True)
                color = unique[np.argmax(counts)]

                if is_tile((col, row), color):
                    set_of_tiles.add((col, row))
                    info[:, :, 0], info[:, :, 1], info[:, :, 2] = color
                else:
                    info[:, :, 0], info[:, :, 1], info[:, :, 2] = (0, 0, 0)

                color_table[(col, row)] = color

                if config.development_recording:  # pragma: no cover
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.33
                    if (col, row) in set_of_tiles:
                        font_color = (170, 255, 255)
                        info[:, :, 2] = 255
                    else:
                        font_color = (24, 1, 255)
                        # reduced[:, :, 2] = 40  # dim ignored tiles
                    info = cv2.putText(info, f'{color[0]}', (1, 10), font, font_scale, font_color, 1, cv2.FILLED)  # (H)SV
                    info = cv2.putText(info, f'{color[1]}', (1, 20), font, font_scale, font_color, 1, cv2.FILLED)  # H(S)V
                    # segment = cv2.putText(segment, f'{color[2]}', (1, 30), font, fontScale, font_color, 1, cv2.FILLED) # HS(V)
                result[px_col + 1 : px_col + grid_h - 1, px_row + 1 : px_row + grid_w - 1] = info
            return color_table

        # image = cv2.erode(_image, None, iterations=2)
        img = cv2.bilateralFilter(_image, 5, 75, 75)
        img = cv2.resize(img, (400, 400), interpolation=cv2.INTER_NEAREST)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        result = np.zeros(hsv.shape, dtype='uint8')

        color_table: dict = {}
        partitions = [
            set(product(range(0, 5), range(0, 15))),
            set(product(range(5, 10), range(0, 15))),
            set(product(range(10, 15), range(0, 15))),
        ]
        tiles1: set = set()
        tiles2: set = set()
        tiles3: set = set()
        future1 = pool.submit(filter_set_of_positions, partitions[0], hsv, result, color_table, tiles1)
        future2 = pool.submit(filter_set_of_positions, partitions[1], hsv, result, color_table, tiles2)
        filter_set_of_positions(partitions[2], hsv, result, color_table, tiles3)
        futures.wait({future1, future2})

        set_of_tiles = tiles1 | tiles2 | tiles3

        logging.debug(f'color table:\n{cls.log_color_table(color_table=color_table, candidates=set_of_tiles)}')

        result = cv2.cvtColor(result, cv2.COLOR_HSV2BGR)
        result = cv2.hconcat([img, result])  # type: ignore
        if any(x in set_of_tiles for x in [(6, 7), (7, 6), (8, 7), (7, 8)]):
            logging.debug(f'candidates:\n{cls.log_candidates(set_of_tiles)}')
            return result, set_of_tiles
        logging.debug('no word detected')
        return result, set()


# test and debug
def main():  # pylint: disable=too-many-locals
    """main function for test and debug"""

    import sys

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        force=True,
        format='%(asctime)s [%(levelname)-1.1s] %(funcName)-15s: %(message)s',
    )

    files = [
        'test/game01/image-21.jpg',
        'test/game02/image-21.jpg',
        'test/game03/image-21.jpg',
        'test/game04/image-21.jpg',
        'test/game05/image-21.jpg',
        'test/game06/image-21.jpg',
        'test/game12/board-19.png',
        'test/game13/23113-180628-30.jpg',
        'test/game14/image-30.jpg',
        'test/game2023DM-01/image-24.jpg',
        'ignore/bild.jpg',
        'ignore/scrabble-gelb.jpg',
        'ignore/scrabble-dunkel.jpg',
        'ignore/dark.jpg',
        'test/board2012/err-03.png',
        'test/board2012/err-11.png',
    ]

    config.config.set('development', 'recording', 'True')
    for fn in files:
        image = cv2.imread(fn)
        warped = Custom2012kBoard.warp(image)
        result, _ = Custom2012kBoard.filter_image(_image=warped.copy())
        cv2.imshow(f'{fn}', result)  # type: ignore
        cv2.waitKey()
        cv2.destroyWindow(f'{fn}')


if __name__ == '__main__':
    main()
