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


class Custom2020Board(CustomBoard):
    """Implementation custom 2020 scrabble board analysis"""

    # layout 2020 dark
    TLETTER = [[160, 200, 100], [180, 255, 255]]
    DLETTER = [[50, 40, 0], [140, 255, 180]]
    TWORD = [[10, 120, 90], [50, 255, 200]]
    DWORD = [[0, 200, 100], [40, 255, 255]]
    FIELD = [[70, 0, 0], [110, 220, 200]]

    # TILES_THRESHOLD = 1000 # use configured threshold
    BOARD_MASK_BORDER = 0
