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

# pylint: disable=duplicate-code
from __future__ import annotations

import logging

import cv2
import imutils
import numpy as np
from cv2.typing import MatLike

from config import DOUBLE_LETTER, DOUBLE_WORDS, TRIPLE_LETTER, TRIPLE_WORDS, config
from game_board.board import GRID_H, GRID_W, OFFSET
from util import TWarp, runtime_measure

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

THRESHOLD_MAX_DIFF = 70

logger = logging.getLogger(__name__)


class CustomBoard:
    """Implementation custom scrabble board analysis"""

    # layout 2012
    TLETTER = [[95, 80, 20], [130, 255, 255]]  # 205 => 102 (-7, +28)
    DLETTER = [[95, 60, 20], [130, 255, 255]]
    TWORD = [[145, 80, 10], [180, 255, 255], [0, 80, 10], [10, 255, 255]]  # 360 => 180 (-35, +10)
    DWORD = [[145, 50, 10], [180, 255, 255], [0, 80, 10], [10, 255, 255]]
    FIELD = [[30, 85, 20], [90, 255, 255]]  # 140 => 70  (-40, + 20)

    SATURATION = [[0, 110, 0], [180, 255, 255]]

    BOARD_MASK_BORDER = 5
    TWORD_MASK, DWORD_MASK, TLETTER_MASK, DLETTER_MASK, FIELD_MASK = None, None, None, None, None
    last_warp: TWarp | None = None

    @classmethod
    def warp(cls, image: MatLike) -> MatLike:  # pylint: disable=too-many-locals
        """ " implement warp of a custom board"""

        rect = cls.find_board(image)

        # construct our destination points which will be used to
        # map the screen to a top-down, "birds eye" view
        dst = np.array([[0, 0], [800, 0], [800, 800], [0, 800]], dtype='float32')

        # calculate the perspective transform matrix and warp
        # the perspective to grab the screen
        cls.last_warp = rect
        matrix = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(image, matrix, (800, 800), flags=cv2.INTER_AREA)

    @classmethod
    def filter_image(cls, color: MatLike) -> tuple[MatLike | None, set]:  # pylint: disable=too-many-locals
        """implement filter for game board"""

        def create_mask(hsv: MatLike, color_range, board_mask) -> np.ndarray:
            tmp = cv2.bitwise_and(hsv, hsv, mask=board_mask)
            mask = np.zeros((800, 800), dtype='uint8')
            for i in range(0, len(color_range), 2):
                mask |= cv2.inRange(tmp, np.array(color_range[i]), np.array(color_range[i + 1]))
            return mask

        def filter_color(hsv: MatLike) -> np.ndarray:
            mask_tword = create_mask(hsv, cls.TWORD, cls.TWORD_MASK)
            mask_dword = create_mask(hsv, cls.DWORD, cls.DWORD_MASK)
            mask_tletter = create_mask(hsv, cls.TLETTER, cls.TLETTER_MASK)
            mask_dletter = create_mask(hsv, cls.DLETTER, cls.DLETTER_MASK)
            mask_field = create_mask(hsv, cls.FIELD, cls.FIELD_MASK)
            return mask_tword | mask_dword | mask_tletter | mask_dletter | mask_field

        def dynamic_threshold(image: MatLike) -> np.ndarray:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)

            # Thresholding for gray image
            segment = gray_blur[
                int(OFFSET + (7 * GRID_H)) : int(OFFSET + (7 * GRID_H)) + GRID_H,
                int(OFFSET + (7 * GRID_W)) : int(OFFSET + (7 * GRID_W)) + GRID_W,
            ]
            threshold_center, _ = cv2.threshold(segment, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            segment = gray_blur[int(OFFSET) : int(OFFSET) + (GRID_H * 14), int(OFFSET) : int(OFFSET) + (GRID_W * 14)]
            threshold_board, _ = cv2.threshold(gray_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            diff = abs(threshold_board - threshold_center)
            alpha = min(diff / THRESHOLD_MAX_DIFF, 1.0)
            final_thresh = alpha * threshold_center + (1 - alpha) * threshold_board

            logger.debug(f'{threshold_center=} {threshold_board=} use={int(final_thresh)}')
            _, thresh = cv2.threshold(gray_blur, int(final_thresh), 255, cv2.THRESH_BINARY_INV)
            return thresh

        if cls.TWORD_MASK is None:
            cls.TWORD_MASK, cls.DWORD_MASK, cls.TLETTER_MASK, cls.DLETTER_MASK, cls.FIELD_MASK = cls.create_board_masks()
        img = cv2.blur(color, (3, 3))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        mask_saturation = cv2.inRange(hsv, np.array(cls.SATURATION[0]), np.array(cls.SATURATION[1]))
        mask_color = filter_color(hsv)

        if config.board.dynamic_threshold:
            mask_result = mask_color | dynamic_threshold(color)
        else:
            mask_result = mask_saturation | mask_color

        mask_result = cv2.bitwise_not(mask_result)  # type: ignore
        candidates = set()
        filtered_pixels = {}
        for col in range(15):
            for row in range(15):
                px_col = int(OFFSET + (row * GRID_H))
                px_row = int(OFFSET + (col * GRID_W))
                segment = mask_result[px_col + 2 : px_col + GRID_H - 2, px_row + 2 : px_row + GRID_W - 2]
                number_of_not_black_pix: int = np.sum(segment > 10)
                filtered_pixels[(col, row)] = number_of_not_black_pix
                if number_of_not_black_pix > config.board.tiles_threshold:
                    candidates.add((col, row))
        result = None
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'filtered pixels:\n{cls.log_pixels(filtered_pixels=filtered_pixels)}')
            logger.debug(f'candidates:\n{cls.log_candidates(candidates=candidates)}')
        return result, candidates

    @staticmethod
    def log_pixels(filtered_pixels: dict) -> str:
        """Print candidates set"""
        board_size = 15
        tmp = '  |' + ''.join(f'{i + 1:5d} ' for i in range(board_size)) + '\n'
        tmp += '\n'.join(
            [
                f'{chr(ord("A") + row)} |{"".join(f" {filtered_pixels[(col, row)]:4d} " for col in range(board_size))}|'
                for row in range(board_size)
            ]
        )
        return tmp

    @staticmethod
    def log_candidates(candidates: set) -> str:
        """Print candidates set"""
        board_size = 15
        tmp = '  |' + ''.join(f'{i + 1:2d} ' for i in range(board_size)) + '\n'
        tmp += '\n'.join(
            [
                f'{chr(ord("A") + row)} |{"".join(" X " if (col, row) in candidates else " · " for col in range(board_size))}|'
                for row in range(board_size)
            ]
        )
        return tmp

    @classmethod
    def create_board_masks(cls) -> tuple[MatLike, MatLike, MatLike, MatLike, MatLike]:
        """create board masks for custom board"""

        tword = np.zeros((800, 800), dtype='uint8')
        dword = np.zeros((800, 800), dtype='uint8')
        tletter = np.zeros((800, 800), dtype='uint8')
        dletter = np.zeros((800, 800), dtype='uint8')
        field = np.zeros((800, 800), dtype='uint8')
        field[:] = 255
        for col in range(15):
            for row in range(15):
                px_col = int(OFFSET + (row * GRID_H))
                px_row = int(OFFSET + (col * GRID_W))
                if (col, row) in TRIPLE_WORDS:
                    tword[
                        px_col - cls.BOARD_MASK_BORDER : px_col + GRID_H + cls.BOARD_MASK_BORDER,
                        px_row - cls.BOARD_MASK_BORDER : px_row + GRID_W + cls.BOARD_MASK_BORDER,
                    ] = 255
                    field[px_col - 0 : px_col + GRID_H + 0, px_row - 0 : px_row + GRID_W + 0] = 0
                elif (col, row) in DOUBLE_WORDS:
                    dword[
                        px_col - cls.BOARD_MASK_BORDER : px_col + GRID_H + cls.BOARD_MASK_BORDER,
                        px_row - cls.BOARD_MASK_BORDER : px_row + GRID_W + cls.BOARD_MASK_BORDER,
                    ] = 255
                    field[px_col - 0 : px_col + GRID_H + 0, px_row - 0 : px_row + GRID_W + 0] = 0
                elif (col, row) in TRIPLE_LETTER:
                    tletter[
                        px_col - cls.BOARD_MASK_BORDER : px_col + GRID_H + cls.BOARD_MASK_BORDER,
                        px_row - cls.BOARD_MASK_BORDER : px_row + GRID_W + cls.BOARD_MASK_BORDER,
                    ] = 255
                    field[px_col - 0 : px_col + GRID_H + 0, px_row - 0 : px_row + GRID_W + 0] = 0
                elif (col, row) in DOUBLE_LETTER:
                    dletter[
                        px_col - cls.BOARD_MASK_BORDER : px_col + GRID_H + cls.BOARD_MASK_BORDER,
                        px_row - cls.BOARD_MASK_BORDER : px_row + GRID_W + cls.BOARD_MASK_BORDER,
                    ] = 255
                    field[px_col - 0 : px_col + GRID_H + 0, px_row - 0 : px_row + GRID_W + 0] = 0
        return tword, dword, tletter, dletter, field

    @staticmethod
    def find_board(image: MatLike) -> TWarp:
        """try to find the game board border"""
        if config.video.warp_coordinates is not None:
            rect = np.array(config.video.warp_coordinates, dtype='float32')
        else:
            # based on: https://www.pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/
            (blue, _, _) = cv2.split(image.copy())

            # Otsu's thresholding after Gaussian filtering
            blur = cv2.GaussianBlur(blue, (5, 5), 0)
            _, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
            dilated = cv2.dilate(th3, kernel)

            cnts = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)  # type: ignore[assignment, arg-type]
            pts = None
            for contour in cnts:
                peri = cv2.arcLength(contour, True)  # type: ignore[arg-type]
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)  # type: ignore[arg-type]
                if len(approx) == 4:
                    pts = approx.reshape(4, 2)
                    break
            rect = np.zeros((4, 2), dtype='float32')
            if pts is None:
                rect[0] = [0, 0]
                rect[1] = [image.shape[1] - 1, 0]
                rect[2] = [image.shape[1] - 1, image.shape[0] - 1]
                rect[3] = [0, image.shape[0] - 1]
                return rect
            # the top-left point has the smallest sum whereas the
            # bottom-right has the largest sum
            sums = pts.sum(axis=1)
            rect[0] = pts[np.argmin(sums)]
            rect[2] = pts[np.argmax(sums)]

            # compute the difference between the points -- the top-right
            # will have the minumum difference and the bottom-left will
            # have the maximum difference
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
        return rect


class Custom2012Board(CustomBoard):
    """Implementation custom 2012 scrabble board analysis"""

    # layout 2012
    # TLETTER = [[95, 80, 20], [130, 255, 255]]  # 205 => 102 (-7, +28)
    # DLETTER = [[95, 60, 20], [130, 255, 255]]
    # TWORD = [[145, 80, 10], [180, 255, 255], [0, 80, 10], [10, 255, 255]]  # 360 => 180 (-35, +10)
    # DWORD = [[145, 50, 10], [180, 255, 255], [0, 80, 10], [10, 255, 255]]
    # FIELD = [[30, 85, 20], [90, 255, 255]]  # 140 => 70  (-40, + 20)

    # SATURATION = [[0, 110, 0], [180, 255, 255]]
    # TILES_THRESHOLD = config.board_tiles_threshold


class Custom2020Board(CustomBoard):
    """Implementation custom 2020 scrabble board analysis"""

    # layout 2020 dark
    TLETTER = [[160, 200, 100], [180, 255, 255]]
    DLETTER = [[50, 40, 0], [140, 255, 180]]
    TWORD = [[10, 120, 90], [50, 255, 200]]
    DWORD = [[0, 200, 100], [40, 255, 255]]
    FIELD = [[70, 0, 0], [110, 220, 200]]

    BOARD_MASK_BORDER = 0


class Custom2020LightBoard(CustomBoard):
    """Implementation custom 2020 light scrabble board analysis"""

    # layout 2020 light
    TLETTER = [[160, 200, 100], [180, 255, 255]]
    DLETTER = [[50, 40, 0], [140, 255, 180]]
    TWORD = [[10, 80, 50], [50, 255, 255]]
    DWORD = [[0, 160, 60], [40, 255, 255]]
    FIELD = [[70, 0, 0], [110, 220, 200]]

    BOARD_MASK_BORDER = 0


## delegates
BOARD_CLASSES = {'custom2012': Custom2012Board, 'custom2020': Custom2020Board, 'custom2020light': Custom2020LightBoard}


def get_last_warp() -> TWarp | None:
    """Delegates the warp of the ``img`` according to the configured board style"""
    return BOARD_CLASSES.get(config.board.layout, Custom2012Board).last_warp


def clear_last_warp() -> None:
    """Delegates the last_warp according to the configured board style"""
    BOARD_CLASSES.get(config.board.layout, Custom2012Board).last_warp = None


@runtime_measure
def warp_image(img: MatLike) -> tuple[MatLike, MatLike]:
    """Delegates the warp of the ``img`` according to the configured board style"""
    warped = BOARD_CLASSES.get(config.board.layout, Custom2012Board).warp(img) if config.video.warp else img
    return warped, cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)


@runtime_measure
def filter_image(img: MatLike) -> tuple[MatLike | None, set]:
    """Delegates the image filter of the ``img`` according to the configured board style"""
    return BOARD_CLASSES.get(config.board.layout, Custom2012Board).filter_image(img)
