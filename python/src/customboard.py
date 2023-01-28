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

import cv2
import numpy as np

from config import config
from game_board.board import (DOUBLE_LETTER, DOUBLE_WORDS, GRID_H, GRID_W, OFFSET,
                              TRIPLE_LETTER, TRIPLE_WORDS)
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


green_lower = np.array([20, 75, 35])
green_upper = np.array([100, 255, 255])
blue_lower = np.array([90, 80, 50])
blue_upper = np.array([150, 255, 255])
red_lower = np.array([0, 80, 50])
red_upper = np.array([10, 255, 255])
red_lower1 = np.array([120, 50, 50])
red_upper1 = np.array([180, 255, 255])


class CustomBoard(GameBoard):
    """ Implentation custom scrabble board analysis """
    last_warp = None

    @staticmethod
    def warp(__image: Mat) -> Mat:
        """" implement warp of a custom board """

        rect = CustomBoard.find_board(__image)

        # construct our destination points which will be used to
        # map the screen to a top-down, "birds eye" view
        dst = np.array([
            [0, 0],
            [800, 0],
            [800, 800],
            [0, 800]], dtype="float32")

        # calculate the perspective transform matrix and warp
        # the perspective to grab the screen
        CustomBoard.last_warp = rect
        matrix = cv2.getPerspectiveTransform(rect, dst)
        result = cv2.warpPerspective(__image, matrix, (800, 800))
        return result

    @staticmethod
    def _is_tile(coord: tuple[int, int], color: tuple[int, int, int]) -> bool:
        if color[1] < 60:  # this is a grey image
            return True
        elif color[1] < 90:  # and color[2] > 165:  # maybe a grey image
            # return True
            if coord in TRIPLE_WORDS or coord in DOUBLE_WORDS:  # check for red
                if (red_lower[0] <= color[0] <= red_upper[0] and red_lower[1] <= color[1] and red_lower[2] <= color[2]) \
                        or (red_lower1[0] <= color[0] <= red_upper1[0]
                            and red_lower1[1] <= color[1] and red_lower1[2] <= color[2]):  # noqa: W503
                    return False
            elif coord in TRIPLE_LETTER or coord in DOUBLE_LETTER:  # check for blue
                if blue_lower[0] <= color[0] <= blue_upper[0] \
                        and blue_lower[1] <= color[1] \
                        and blue_lower[2] <= color[2]:
                    return False
            else:  # check for green
                if green_lower[0] <= color[0] <= green_upper[0] \
                        and green_lower[1] <= color[1] \
                        and green_lower[2] <= color[2]:
                    return False
            return True
        return False

    @staticmethod
    def _filter_set_of_positions(coord: set, img: Mat, result: Mat, color_table: dict) -> dict:
        offset = int(OFFSET / 2)  # use 400x400 instead of 800x800
        grid_h = int(GRID_H / 2)
        grid_w = int(GRID_W / 2)
        for (col, row) in coord:
            px_col = int(offset + (row * grid_h))
            px_row = int(offset + (col * grid_w))
            segment = img[px_col + 1:px_col + grid_h - 1, px_row + 1:px_row + grid_w - 1]
            data = segment.reshape((-1, 3))
            data = np.float32(data)  # type: ignore

            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 8, 1.0)
            k = 4
            _, label, center = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            reduced = np.uint8(center)[label.flatten()]  # type: ignore
            reduced = reduced.reshape((segment.shape))
            unique, counts = np.unique(reduced.reshape(-1, 3), axis=0, return_counts=True)
            color = unique[np.argmax(counts)]

            color_table[(col, row)] = color
            segment[:, :, 0], segment[:, :, 1], segment[:, :, 2] = color

            if config.development_recording:
                font = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 0.33
                if CustomBoard._is_tile((col, row), color):
                    font_color = (170, 255, 255)
                    segment[:, :, 2] = 255
                else:
                    font_color = (24, 1, 255)
                    # reduced[:, :, 2] = 40  # dim ignored tiles
                segment = cv2.putText(segment, f'{color[0]}', (1, 10), font, fontScale, font_color, 1, cv2.FILLED)  # (H)SV
                segment = cv2.putText(segment, f'{color[1]}', (1, 20), font, fontScale, font_color, 1, cv2.FILLED)  # H(S)V
                # segment = cv2.putText(segment, f'{color[2]}', (1, 30), font, fontScale, font_color, 1, cv2.FILLED) # HS(V)
            result[px_col + 1:px_col + grid_h - 1, px_row + 1:px_row + grid_w - 1] = segment
        return color_table

    @staticmethod
    def filter_image(_image: Mat) -> tuple[Mat, set]:
        """ implement filter for custom board """

        # image = cv2.erode(_image, None, iterations=2)
        img = cv2.bilateralFilter(_image, 5, 75, 75)
        img = cv2.resize(img, (400, 400), interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        result = np.zeros(hsv.shape, dtype="uint8")

        color_table: dict = {}
        partitions = [set(product(range(0, 5), range(0, 15))),
                      set(product(range(5, 10), range(0, 15))),
                      set(product(range(10, 15), range(0, 15)))]
        future1 = pool.submit(CustomBoard._filter_set_of_positions, partitions[0], hsv, result, color_table)
        future2 = pool.submit(CustomBoard._filter_set_of_positions, partitions[1], hsv, result, color_table)
        CustomBoard._filter_set_of_positions(partitions[2], hsv, result, color_table)
        futures.wait({future1, future2})

        set_of_tiles = set()
        for col, row in product(range(0, 15), range(0, 15)):
            if CustomBoard._is_tile((col, row), color_table[(col, row)]):
                set_of_tiles.add((col, row))

        result = cv2.cvtColor(result, cv2.COLOR_HSV2BGR)
        result = cv2.hconcat([img, result])  # type: ignore
        if any(x in set_of_tiles for x in [(6, 7), (7, 6), (8, 7), (7, 8)]):
            logging.debug(f'candidates {set_of_tiles}')
            return result, set_of_tiles
        else:
            logging.debug('no word detected')
            return result, set()
