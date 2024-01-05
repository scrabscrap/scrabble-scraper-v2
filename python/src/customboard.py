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

import cv2
import numpy as np

from game_board.board import (DOUBLE_LETTER, DOUBLE_WORDS, GRID_H, GRID_W,
                              OFFSET, TRIPLE_LETTER, TRIPLE_WORDS)
from gameboard import GameBoard

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


def _create_masks() -> tuple[Mat, Mat, Mat, Mat, Mat]:
    tword = np.zeros((800, 800), dtype="uint8")
    dword = np.zeros((800, 800), dtype="uint8")
    tletter = np.zeros((800, 800), dtype="uint8")
    dletter = np.zeros((800, 800), dtype="uint8")
    field = np.zeros((800, 800), dtype="uint8")
    field[:] = 255
    for col in range(15):
        for row in range(15):
            px_col = int(OFFSET + (row * GRID_H))
            px_row = int(OFFSET + (col * GRID_W))
            if (col, row) in TRIPLE_WORDS:
                tword[px_col - 5:px_col + GRID_H + 5, px_row - 5:px_row + GRID_W + 5] = 255
                field[px_col - 0:px_col + GRID_H + 0, px_row - 0:px_row + GRID_W + 0] = 0
            elif (col, row) in DOUBLE_WORDS:
                dword[px_col - 5:px_col + GRID_H + 5, px_row - 5:px_row + GRID_W + 5] = 255
                field[px_col - 0:px_col + GRID_H + 0, px_row - 0:px_row + GRID_W + 0] = 0
            elif (col, row) in TRIPLE_LETTER:
                tletter[px_col - 5:px_col + GRID_H + 5, px_row - 5:px_row + GRID_W + 5] = 255
                field[px_col - 0:px_col + GRID_H + 0, px_row - 0:px_row + GRID_W + 0] = 0
            elif (col, row) in DOUBLE_LETTER:
                dletter[px_col - 5:px_col + GRID_H + 5, px_row - 5:px_row + GRID_W + 5] = 255
                field[px_col - 0:px_col + GRID_H + 0, px_row - 0:px_row + GRID_W + 0] = 0
    return tword, dword, tletter, dletter, field


board_tword, board_dword, board_tletter, board_dletter, board_field = _create_masks()


class CustomBoard(GameBoard):
    """ Implementation custom scrabble board analysis """

    # layout 2012
    TLETTER = [[95, 80, 20], [130, 255, 255]]                                # 205 => 102 (-7, +28)
    DLETTER = [[95, 60, 20], [130, 255, 255]]
    TWORD = [[145, 80, 10], [180, 255, 255], [0, 80, 10], [10, 255, 255]]    # 360 => 180 (-35, +10)
    DWORD = [[145, 50, 10], [180, 255, 255], [0, 80, 10], [10, 255, 255]]
    FIELD = [[30, 85, 20], [90, 255, 255]]                                   # 140 => 70  (-40, + 20)

    SATURATION = [[0, 110, 0], [180, 255, 255]]
    TILES_THRESHOLD = 1200

    last_warp = None

    @classmethod
    def warp(cls, __image: Mat) -> Mat:  # pylint: disable=too-many-locals
        """" implement warp of a custom board """

        rect = cls.find_board(__image)

        # construct our destination points which will be used to
        # map the screen to a top-down, "birds eye" view
        dst = np.array([
            [0, 0],
            [800, 0],
            [800, 800],
            [0, 800]], dtype="float32")

        # calculate the perspective transform matrix and warp
        # the perspective to grab the screen
        cls.last_warp = rect
        matrix = cv2.getPerspectiveTransform(rect, dst)
        result = cv2.warpPerspective(__image, matrix, (800, 800))
        return result

    @classmethod
    def log_candidates(cls, candidates) -> str:
        """Print candidates set"""
        board_size = 15
        tmp = '   ' + ' '.join(f' {i + 1:2d}' for i in range(board_size)) + '  \n'
        tmp += '\n'.join([
            f"{chr(ord('A') + row)} | {' '.join(' X ' if (col, row) in candidates else ' . ' for col in range(board_size))} |"
            for row in range(board_size)
        ])
        return tmp

    @classmethod
    def filter_image(cls, _image: Mat) -> tuple[Mat, set]:  # pylint: disable=too-many-locals

        img = cv2.medianBlur(_image, 5)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask_saturation = cv2.inRange(hsv, np.array(cls.SATURATION[0]), np.array(cls.SATURATION[1]))

        tmp = cv2.bitwise_and(hsv, hsv, mask=board_tword)
        mask_tword = np.zeros((800, 800), dtype="uint8")
        for i in range(0, len(cls.TWORD), 2):
            mask_tword |= cv2.inRange(tmp, np.array(cls.TWORD[i]), np.array(cls.TWORD[i + 1]))

        tmp = cv2.bitwise_and(hsv, hsv, mask=board_dword)
        mask_dword = np.zeros((800, 800), dtype="uint8")
        for i in range(0, len(cls.DWORD), 2):
            mask_dword |= cv2.inRange(tmp, np.array(cls.DWORD[i]), np.array(cls.DWORD[i + 1]))

        tmp = cv2.bitwise_and(hsv, hsv, mask=board_tletter)
        mask_tletter = np.zeros((800, 800), dtype="uint8")
        for i in range(0, len(cls.TLETTER), 2):
            mask_tletter |= cv2.inRange(tmp, np.array(cls.TLETTER[i]), np.array(cls.TLETTER[i + 1]))

        tmp = cv2.bitwise_and(hsv, hsv, mask=board_dletter)
        mask_dletter = np.zeros((800, 800), dtype="uint8")
        for i in range(0, len(cls.DLETTER), 2):
            mask_dletter |= cv2.inRange(tmp, np.array(cls.DLETTER[i]), np.array(cls.DLETTER[i + 1]))

        tmp = cv2.bitwise_and(hsv, hsv, mask=board_field)
        mask_field = np.zeros((800, 800), dtype="uint8")
        for i in range(0, len(cls.FIELD), 2):
            mask_field |= cv2.inRange(tmp, np.array(cls.FIELD[i]), np.array(cls.FIELD[i + 1]))

        mask_result = mask_saturation | mask_tword | mask_dword | mask_tletter | mask_dletter | mask_field
        mask_result = cv2.bitwise_not(mask_result)
        candidates = set()
        for col in range(15):
            for row in range(15):
                px_col = int(OFFSET + (row * GRID_H))
                px_row = int(OFFSET + (col * GRID_W))
                segment = mask_result[px_col + 2:px_col + GRID_H - 2, px_row + 2:px_row + GRID_W - 2]
                number_of_not_black_pix = np.sum(segment != 0)
                if number_of_not_black_pix > cls.TILES_THRESHOLD:
                    candidates.add((col, row))
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            result = cv2.hconcat([mask_saturation, mask_tword, mask_dword,
                                  mask_field, mask_tletter, mask_dletter, mask_result])
            logging.debug(f'candidates:\n{cls.log_candidates(candidates=candidates)}')
        else:
            result = None
        return result, candidates
