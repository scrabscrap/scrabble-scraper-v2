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

from customboard import CustomBoard


class Custom2020LightBoard(CustomBoard):
    """Implementation custom 2020 light scrabble board analysis"""

    # hsv 0-180, 0-255, 0-255
    # color_triple_letter = np.array([168, 66, 214])
    # color_double_letter = np.array([116, 69, 133])
    # color_triple_word = np.array([29, 166, 204])
    # color_double_word = np.array([21, 133, 255])
    # color_field = np.array([97, 145, 156])

    # layout 2020 light
    TLETTER = [[160, 200, 100], [180, 255, 255]]
    DLETTER = [[50, 40, 0], [140, 255, 180]]
    TWORD = [[10, 80, 50], [50, 255, 255]]
    DWORD = [[0, 160, 60], [40, 255, 255]]
    FIELD = [[70, 0, 0], [110, 220, 200]]

    BOARD_MASK_BORDER = 0
