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
from cv2.typing import MatLike

from game_board.board import GRID_H, GRID_W, get_x_position, get_y_position
from gameboard import GameBoard

# dimensions board classic
# ------------------------
# overall size: 360mm x 360mm
# grid: 310mm x 310mm
# top: 17mm
# left: 25mm
# right: 25mm
# bottom: 33mm
#
# tiles
# -------------
# 19mm x 19mm


class ClassicBoard(GameBoard):
    """Implementation classic scrabble board analysis"""

    last_warp = None

    def __init__(self):
        pass

    @classmethod
    def warp(cls, __image: MatLike) -> MatLike:  # pylint: disable=too-many-locals
        """ " implement warp of a classic board"""

        rect = ClassicBoard.find_board(__image)

        # now that we have our rectangle of points, let's compute
        # the width of our new image
        (topleft, topright, bottomright, bottomleft) = rect
        width_a = np.sqrt(((bottomright[0] - bottomleft[0]) ** 2) + ((bottomright[1] - bottomleft[1]) ** 2))
        width_b = np.sqrt(((topright[0] - topleft[0]) ** 2) + ((topright[1] - topleft[1]) ** 2))

        # ...and now for the height of our new image
        height_a = np.sqrt(((topright[0] - bottomright[0]) ** 2) + ((topright[1] - bottomright[1]) ** 2))
        height_b = np.sqrt(((topleft[0] - bottomleft[0]) ** 2) + ((topleft[1] - bottomleft[1]) ** 2))

        # take the maximum of the width and height values to reach
        # our final dimensions
        max_width = max(int(width_a), int(width_b))
        max_height = max(int(height_a), int(height_b))

        # construct our destination points which will be used to
        # map the screen to a top-down, "birds eye" view
        dst = np.array([[0, 0], [max_width, 0], [max_width, max_height], [0, max_height]], dtype='float32')

        ClassicBoard.last_warp = rect
        # calculate the perspective transform matrix and warp
        # the perspective to grab the screen
        matrix = cv2.getPerspectiveTransform(rect, dst)
        result = cv2.warpPerspective(__image, matrix, (max_width, max_height))
        # crop bild auf 10mm Rand
        # größe = 360mm x 360mm
        # abschneiden: oben: 7mm links: 15mm rechts 15mm unten 23mm
        # ergibt: 330mm x 330mm
        # img[y:y + h, x:x + w]
        crop_top = int((max_height / 360) * 7)
        crop_width = int((max_width / 360) * 15)
        crop_bottom = int((max_height / 360) * 23)
        crop = result[crop_top : max_height - crop_bottom, crop_width : max_width - crop_width]
        return cv2.resize(crop, (800, 800))

    @classmethod
    def filter_image(cls, _img: MatLike) -> tuple[MatLike, set]:
        """implement filter for classic board"""
        _gray = cv2.cvtColor(_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        blank_grid = 255 - thresh.astype('uint8')
        blank_grid = cv2.erode(blank_grid, None, iterations=4)  # type: ignore[call-overload]
        blank_grid = cv2.dilate(blank_grid, None, iterations=2)  # type: ignore[call-overload]
        blank_grid = cv2.erode(blank_grid, None, iterations=4)  # type: ignore[call-overload]
        blank_grid = cv2.dilate(blank_grid, None, iterations=2)  # type: ignore[call-overload]

        mark_grid = cv2.GaussianBlur(thresh, (5, 5), 0)
        mark_grid = cv2.erode(mark_grid, None, iterations=4)  # type: ignore[call-overload]
        mark_grid = cv2.dilate(mark_grid, None, iterations=4)  # type: ignore[call-overload]
        _, mark_grid = cv2.threshold(mark_grid, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        _tiles_candidates: set = set()
        _blank_candidates: dict = {}
        ClassicBoard._mark_grid((7, 7), mark_grid, blank_grid, _tiles_candidates, _blank_candidates)  # starte in der Mitte
        logging.debug(f'candidates {_tiles_candidates}')
        return _gray, _tiles_candidates

    @classmethod
    def _mark_grid(cls, coord: tuple[int, int], _grid, _blank_grid, _board: set, _blank_candidates: dict):
        (col, row) = coord
        if col not in range(15):
            return
        if row not in range(15):
            return
        if coord in _board:
            return
        _y = get_y_position(row)
        _x = get_x_position(col)
        # schneide Gitterelement aus
        _image = _grid[_y + 12 : _y + GRID_H - 12, _x + 12 : _x + GRID_W - 12]
        percentage = np.count_nonzero(_image) * 100 // _image.size
        if percentage > 60:
            _board.add(coord)
            _img_blank = _blank_grid[_y + 15 : _y + GRID_H - 15, _x + 15 : _x + GRID_W - 15]
            percentage = np.count_nonzero(_img_blank) * 100 // _img_blank.size
            if percentage > 85:
                _blank_candidates[coord] = ('_', 76 + (percentage - 90) * 2)
            cls._mark_grid((col + 1, row), _grid, _blank_grid, _board, _blank_candidates)
            cls._mark_grid((col - 1, row), _grid, _blank_grid, _board, _blank_candidates)
            cls._mark_grid((col, row + 1), _grid, _blank_grid, _board, _blank_candidates)
            cls._mark_grid((col, row - 1), _grid, _blank_grid, _board, _blank_candidates)
