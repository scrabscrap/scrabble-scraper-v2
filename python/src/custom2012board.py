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

from customboard import CustomBoard


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
