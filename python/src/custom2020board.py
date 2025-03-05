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

from typing import Set, Tuple

import numpy as np

from customboard import CustomBoard
from game_board.board import DOUBLE_LETTER, DOUBLE_WORDS, GRID_H, GRID_W, OFFSET, TRIPLE_LETTER, TRIPLE_WORDS


def _create_masks() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    def create_mask(shape=(800, 800)) -> np.ndarray:
        return np.zeros(shape, dtype='uint8')

    def apply_mask(
        mask: np.ndarray, coordinates: Set[Tuple[int, int]], grid_h: int, grid_w: int, offset: int, field: np.ndarray
    ):  # pylint: disable=too-many-arguments, too-many-positional-arguments
        for col, row in coordinates:
            px_col, px_row = int(offset + row * grid_h), int(offset + col * grid_w)
            mask[px_col : px_col + grid_h, px_row : px_row + grid_w] = 255
            field[px_col : px_col + grid_h, px_row : px_row + grid_w] = 0

    field = np.full((800, 800), 255, dtype='uint8')
    masks = {'tword': create_mask(), 'dword': create_mask(), 'tletter': create_mask(), 'dletter': create_mask()}

    for key, coords in zip(masks.keys(), [TRIPLE_WORDS, DOUBLE_WORDS, TRIPLE_LETTER, DOUBLE_LETTER]):
        apply_mask(masks[key], coords, GRID_H, GRID_W, OFFSET, field)

    return masks['tword'], masks['dword'], masks['tletter'], masks['dletter'], field


board_tword, board_dword, board_tletter, board_dletter, board_field = _create_masks()


class Custom2020Board(CustomBoard):
    """Implementation custom 2020 scrabble board analysis"""

    # layout 2020 dark
    TLETTER = [[160, 200, 100], [180, 255, 255]]
    DLETTER = [[50, 40, 0], [140, 255, 180]]
    TWORD = [[10, 120, 90], [50, 255, 200]]
    DWORD = [[0, 200, 100], [40, 255, 255]]
    FIELD = [[70, 0, 0], [110, 220, 200]]

    # TILES_THRESHOLD = 1000 # use configured threshold
