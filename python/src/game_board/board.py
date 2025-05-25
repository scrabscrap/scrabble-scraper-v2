"""
This file is part of the scrabble-scraper-v2 distribution
(https://github.com/scrabscrap/scrabble-scraper-v2)
Copyright (c) 2020 Rainer Rohloff.

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

import cv2
from numpy import ndarray

# target layout
# board
# -------------------------------
# overall size: 800px x 800px
# top, left, right, bottom: 25px
# grid: 750px x 750px
#
# tiles
# -----
# 46px x 46px

# calculation of the fields
# -------------------------
# from row/column (0..14) to px (25..750)
# y = 25 + (row * 50)
# x = 25 + (col * 50)

# from px (0..800) to row/column (0..14)
# row = (y - 25) // 50
# col = (x - 25) // 50


# triple words/double words/triple letter/double letter field coordinates
TRIPLE_WORDS = {(0, 0), (7, 0), (14, 0), (0, 7), (14, 7), (0, 14), (7, 14), (14, 14)}
DOUBLE_WORDS = {(1, 1),(13, 1), (2, 2), (12, 2), (3, 3), (11, 3), (4, 4), (10, 4), (7, 7),
                (4, 10),(10, 10),(3, 11),(11, 11),(2, 12), (12, 12), (1, 13),(13, 13), }  # fmt: off
TRIPLE_LETTER = {(5, 1), (9, 1), (1, 5), (5, 5), (9, 5), (13, 5), (1, 9), (5, 9), (9, 9), (13, 9), (5, 13), (9, 13)}
DOUBLE_LETTER = {(3, 0),(11, 0), (6, 2), (8, 2), (0, 3), (7, 3), (14, 3), (2, 6), (6, 6), (8, 6),  (12, 6), (3, 7),
                 (11, 7),(2, 8), (6, 8), (8, 8),(12, 8),(0, 11), (7, 11),(14, 11),(6, 12),(8, 12), (3, 14), (11, 14),
                }  # fmt: off

# constants for the target layout
GRID_W = 50
GRID_H = 50
OFFSET = 25


def calc_x_position(x: int) -> int:
    """return 0..14"""
    return int((x - OFFSET) // GRID_W)


def calc_y_position(y: int) -> int:
    """return 0..14"""
    return int((y - OFFSET) // GRID_H)


def get_x_position(pos: int) -> int:
    """return col 25..750"""
    return int(OFFSET + (pos * GRID_W))


def get_y_position(pos: int) -> int:
    """return row 25..750"""
    return int(OFFSET + (pos * GRID_H))


def overlay_grid(image: ndarray) -> ndarray:  # pragma: no cover
    """returns an image with an overlayed grid"""
    img = image.copy()
    x1 = get_x_position(0)
    y1 = get_y_position(0)
    x2 = get_x_position(15)
    y2 = get_y_position(15)
    for x in range(16):
        pos = get_x_position(x)
        cv2.line(img, (pos, y1), (pos, y2), (0, 255, 0), 1)
    for y in range(16):
        pos = get_y_position(y)
        cv2.line(img, (x1, pos), (x2, pos), (0, 255, 0), 1)
    return img


def overlay_tiles(image: ndarray, board: dict[tuple[int, int], tuple[str, int]]) -> ndarray:  # pragma: no cover
    """returns an image with overlayed characters from the board dictionary"""
    img = image.copy()
    for (col, row), (value, _) in board.items():
        cv2.putText(
            img, value, (get_x_position(col) + 5, get_y_position(row) + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2
        )
    return img
