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
import pprint
import logging
from concurrent import futures
from itertools import product

import cv2
import numpy as np

from config import Config
from game_board.board import (DOUBLE_LETTER, DOUBLE_WORDS, GRID_H, GRID_W,
                              OFFSET, TRIPLE_LETTER, TRIPLE_WORDS)
from gameboard import GameBoard
from threadpool import pool

Mat = np.ndarray[int, np.dtype[np.generic]]


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

# tiles [1, 4, 0] , [176, 97]
# green_lower = np.array([30, 85, 35])
# green_upper = np.array([90, 255, 255])
# blue_lower = np.array([90, 70, 50])
# blue_upper = np.array([130, 255, 255])
# red_lower = np.array([0, 100, 50])
# red_upper = np.array([10, 255, 255])
# red_lower1 = np.array([145, 50, 50])
# red_upper1 = np.array([180, 255, 255])

field_lower = np.array([30, 85, 35])
field_upper = np.array([90, 255, 255])

letter_lower = np.array([95, 60, 50])
letter_upper = np.array([130, 255, 255])

word_lower = np.array([0, 100, 50])
word_upper = np.array([10, 255, 255])
word_lower1 = np.array([145, 50, 50])
word_upper1 = np.array([180, 255, 255])


class Custom2012Board(GameBoard):
    """ Implentation custom scrabble board analysis """
    last_warp = None
    statistic: dict = {
        'field-lower': [256, 256, 256],
        'field-upper': [-1, -1, -1],
        'tletter-lower': [256, 256, 256],
        'tletter-upper': [-1, -1, -1],
        'dletter-lower': [256, 256, 256],
        'dletter-upper': [-1, -1, -1],
        'tword-lower': [256, 256, 256],
        'tword-upper': [-1, -1, -1],
        'tword1-lower': [256, 256, 256],
        'tword1-upper': [-1, -1, -1],
        'dword-lower': [256, 256, 256],
        'dword-upper': [-1, -1, -1],
        'dword1-lower': [256, 256, 256],
        'dword1-upper': [-1, -1, -1],
        'tiles-lower': [256, 256, 256],
        'tiles-upper': [-1, -1, -1],
    }

    @staticmethod
    def warp(__image: Mat) -> Mat:  # pylint: disable=too-many-locals
        """" implement warp of a custom board """

        rect = Custom2012Board.find_board(__image)

        # construct our destination points which will be used to
        # map the screen to a top-down, "birds eye" view
        dst = np.array([
            [0, 0],
            [800, 0],
            [800, 800],
            [0, 800]], dtype="float32")

        # calculate the perspective transform matrix and warp
        # the perspective to grab the screen
        Custom2012Board.last_warp = rect
        matrix = cv2.getPerspectiveTransform(rect, dst)
        result = cv2.warpPerspective(__image, matrix, (800, 800))
        return result

    @staticmethod
    def _is_tile(coord: tuple[int, int], color: tuple[int, int, int]) -> bool:  # pylint: disable=too-many-return-statements
        if coord in TRIPLE_WORDS:  # dark red
            if word_lower[0] <= color[0] <= word_upper[0] and \
                    word_lower[1] <= color[1] <= word_upper[1]:
                Custom2012Board.statistic['tword-lower'] = np.minimum(color, Custom2012Board.statistic['tword-lower'])
                Custom2012Board.statistic['tword-upper'] = np.maximum(color, Custom2012Board.statistic['tword-upper'])
                return False
            if word_lower1[0] <= color[0] <= word_upper1[0] and \
                    word_lower1[1] <= color[1] <= word_upper1[1]:
                Custom2012Board.statistic['tword1-lower'] = np.minimum(color, Custom2012Board.statistic['tword1-lower'])
                Custom2012Board.statistic['tword1-upper'] = np.maximum(color, Custom2012Board.statistic['tword1-upper'])
                return False
        elif coord in DOUBLE_WORDS:  # light red
            if word_lower[0] <= color[0] <= word_upper[0] and \
                    word_lower[1] <= color[1] <= word_upper[1]:
                Custom2012Board.statistic['dword-lower'] = np.minimum(color, Custom2012Board.statistic['dword-lower'])
                Custom2012Board.statistic['dword-upper'] = np.maximum(color, Custom2012Board.statistic['dword-upper'])
                return False
            if word_lower1[0] <= color[0] <= word_upper1[0] and \
                    word_lower1[1] <= color[1] <= word_upper1[1]:
                Custom2012Board.statistic['dword1-lower'] = np.minimum(color, Custom2012Board.statistic['dword1-lower'])
                Custom2012Board.statistic['dword1-upper'] = np.maximum(color, Custom2012Board.statistic['dword1-upper'])
                return False
        elif coord in TRIPLE_LETTER:  # dark blue
            if letter_lower[0] <= color[0] <= letter_upper[0] and \
                    letter_lower[1] <= color[1] <= letter_upper[1]:
                Custom2012Board.statistic['tletter-lower'] = np.minimum(color, Custom2012Board.statistic['tletter-lower'])
                Custom2012Board.statistic['tletter-upper'] = np.maximum(color, Custom2012Board.statistic['tletter-upper'])
                return False
        elif coord in DOUBLE_LETTER:  # light blue
            if letter_lower[0] <= color[0] <= letter_upper[0] and \
                    letter_lower[1] <= color[1] <= letter_upper[1]:
                Custom2012Board.statistic['dletter-lower'] = np.minimum(color, Custom2012Board.statistic['dletter-lower'])
                Custom2012Board.statistic['dletter-upper'] = np.maximum(color, Custom2012Board.statistic['dletter-upper'])
                return False
        else:  # green
            if field_lower[0] <= color[0] <= field_upper[0] and \
                    field_lower[1] <= color[1] <= field_upper[1]:
                Custom2012Board.statistic['field-lower'] = np.minimum(color, Custom2012Board.statistic['field-lower'])
                Custom2012Board.statistic['field-upper'] = np.maximum(color, Custom2012Board.statistic['field-upper'])
                return False
        Custom2012Board.statistic['tiles-lower'] = np.minimum(color, Custom2012Board.statistic['tiles-lower'])
        Custom2012Board.statistic['tiles-upper'] = np.maximum(color, Custom2012Board.statistic['tiles-upper'])
        return True

    @staticmethod
    def _filter_set_of_positions(coord: set, img: Mat, result: Mat, color_table: dict, set_of_tiles: set) -> dict:
        # pylint: disable=too-many-locals
        offset = int(OFFSET / 2)  # use 400x400 instead of 800x800
        grid_h = int(GRID_H / 2)
        grid_w = int(GRID_W / 2)
        for (col, row) in coord:
            px_col = int(offset + (row * grid_h))
            px_row = int(offset + (col * grid_w))
            segment = img[px_col + 2:px_col + grid_h - 2, px_row + 2:px_row + grid_w - 2]
            info = img[px_col + 1:px_col + grid_h - 1, px_row + 1:px_row + grid_w - 1]
            # segment[:, :, 2] = 255  # ignore value for kmeas
            data = segment.reshape((-1, 3))
            data = np.float32(data)  # type: ignore

            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 8, 1.0)
            k = 3
            _, label, center = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            reduced = np.uint8(center)[label.flatten()]  # type: ignore # pylint: disable=unsubscriptable-object
            unique, counts = np.unique(reduced.reshape(-1, 3), axis=0, return_counts=True)
            color = unique[np.argmax(counts)]

            if Custom2012Board._is_tile((col, row), color):
                set_of_tiles.add((col, row))
                info[:, :, 0], info[:, :, 1], info[:, :, 2] = color
            else:
                info[:, :, 0], info[:, :, 1], info[:, :, 2] = (0, 0, 0)

            color_table[(col, row)] = color

            if Config.development_recording():  # pragma: no cover
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.33
                if Custom2012Board._is_tile((col, row), color):
                    font_color = (170, 255, 255)
                    info[:, :, 2] = 255
                else:
                    font_color = (24, 1, 255)
                    # reduced[:, :, 2] = 40  # dim ignored tiles
                info = cv2.putText(info, f'{color[0]}', (1, 10), font, font_scale, font_color, 1, cv2.FILLED)  # (H)SV
                info = cv2.putText(info, f'{color[1]}', (1, 20), font, font_scale, font_color, 1, cv2.FILLED)  # H(S)V
                # segment = cv2.putText(segment, f'{color[2]}', (1, 30), font, fontScale, font_color, 1, cv2.FILLED) # HS(V)
            result[px_col + 1:px_col + grid_h - 1, px_row + 1:px_row + grid_w - 1] = info
        return color_table

    @staticmethod
    def log_color_table(color_table, candidates) -> str:
        """print color table"""
        tmp = ''
        for color in range(3):
            tmp += '   '
            for i in range(15):
                tmp += f'{(i + 1):5d} '
            tmp += '  \n'
            for row in range(15):
                tmp += f"{chr(ord('A') + row)} |"
                for col in range(15):
                    if (col, row) in candidates:
                        tmp += f' [{color_table[(col, row)][color]:-3d}]'
                    else:
                        tmp += f'  {color_table[(col, row)][color]:-3d} '
                tmp += ' |\n'
            tmp += '\n'
        return tmp

    @staticmethod
    def log_candidates(candidates) -> str:
        """print candidates set"""
        tmp = '   '
        for i in range(15):
            tmp += f'{(i + 1):2d} '
        tmp += '  \n'
        for row in range(15):
            tmp += f"{chr(ord('A') + row)} |"
            for col in range(15):
                tmp += ' X ' if (col, row) in candidates else ' . '
            tmp += ' |\n'
        return tmp

    @staticmethod
    def filter_image(_image: Mat) -> tuple[Mat, set]:
        """ implement filter for custom board """

        # image = cv2.erode(_image, None, iterations=2)
        img = cv2.bilateralFilter(_image, 5, 75, 75)
        img = cv2.resize(img, (400, 400), interpolation=cv2.INTER_NEAREST)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        result = np.zeros(hsv.shape, dtype="uint8")

        color_table: dict = {}
        partitions = [set(product(range(0, 5), range(0, 15))),
                      set(product(range(5, 10), range(0, 15))),
                      set(product(range(10, 15), range(0, 15)))]
        tiles1: set = set()
        tiles2: set = set()
        tiles3: set = set()
        future1 = pool.submit(Custom2012Board._filter_set_of_positions, partitions[0], hsv, result, color_table, tiles1)
        future2 = pool.submit(Custom2012Board._filter_set_of_positions, partitions[1], hsv, result, color_table, tiles2)
        Custom2012Board._filter_set_of_positions(partitions[2], hsv, result, color_table, tiles3)
        futures.wait({future1, future2})

        set_of_tiles = tiles1 | tiles2 | tiles3

        logging.debug(f'color statistic:\n {pprint.pformat(Custom2012Board.statistic)}')
        logging.debug(f'color table:\n{Custom2012Board.log_color_table(color_table=color_table, candidates=set_of_tiles)}')

        result = cv2.cvtColor(result, cv2.COLOR_HSV2BGR)
        result = cv2.hconcat([img, result])  # type: ignore
        if any(x in set_of_tiles for x in [(6, 7), (7, 6), (8, 7), (7, 8)]):
            logging.debug(f'candidates:\n{Custom2012Board.log_candidates(set_of_tiles)}')
            return result, set_of_tiles
        logging.debug('no word detected')
        return result, set()
