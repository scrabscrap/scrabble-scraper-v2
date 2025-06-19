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

