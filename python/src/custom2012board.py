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
import numpy as np

from customboard import CustomBoard
from game_board.board import DOUBLE_WORDS, TRIPLE_WORDS


class Custom2012Board(CustomBoard):
    """ Implementation custom 2012 scrabble board analysis """

    # FIELD_COLOR = ([30, 85, 10], [90, 255, 255])

    # TLETTER_COLOR = ([95, 60, 10], [130, 255, 255])
    # DLETTER_COLOR = ([95, 60, 10], [130, 255, 255])

    # TWORD_COLOR = ([145, 100, 10], [190, 255, 255])  # H: 0-10 & 145-180
    # DWORD_COLOR = ([145, 100, 10], [190, 255, 255])  # H: 0-10 & 145-180

    TWORD_COLOR1 = ([145, 50, 10], [189, 100, 255])  # overwrite H: 145-189, S: _50_-100
    DWORD_COLOR1 = ([145, 50, 10], [180, 100, 255])  # overwrite H: 145-180, S: _50_-100

    @classmethod
    def _is_tile(cls, coord: tuple[int, int], color: tuple[int, int, int]) -> bool:
        # pylint: disable=too-many-return-statements
        def between(val: tuple[int, int, int], lower: list[int], upper: list[int]) -> bool:
            if upper[0] > 180:
                return (lower[0] <= val[0] or val[0] <= (upper[0] - 180)) and \
                    (lower[1] <= val[1] <= upper[1]) and \
                    (lower[2] <= val[2] <= upper[2])
            return (lower[0] <= val[0] <= upper[0]) and \
                (lower[1] <= val[1] <= upper[1]) and \
                (lower[2] <= val[2] <= upper[2])

        if coord in TRIPLE_WORDS:  # dark red
            if between(color, cls.TWORD_COLOR1[cls.LOWER], cls.TWORD_COLOR1[cls.UPPER]):
                if 'tword1' not in cls.statistic:
                    cls.statistic['tword1'] = ([256, 256, 256], [-1, -1, -1])
                cls.statistic['tword1'] = (np.minimum(color, cls.statistic['tword1'][cls.LOWER]),
                                           np.maximum(color, cls.statistic['tword1'][cls.UPPER]))
                return False
            return super()._is_tile(coord, color)
        if coord in DOUBLE_WORDS:  # light red
            if between(color, cls.DWORD_COLOR1[cls.LOWER], cls.DWORD_COLOR1[cls.UPPER]):
                if 'dword1' not in cls.statistic:
                    cls.statistic['dword1'] = ([256, 256, 256], [-1, -1, -1])
                cls.statistic['dword1'] = (np.minimum(color, cls.statistic['dword1'][cls.LOWER]),
                                           np.maximum(color, cls.statistic['dword1'][cls.UPPER]))
                return False
            return super()._is_tile(coord, color)
        return super()._is_tile(coord, color)
