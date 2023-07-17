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
    """ Implementation custom 2020 scrabble board analysis """

    # hsv 0-180, 0-255, 0-255
    # color_triple_letter = np.array([168, 66, 214])
    # color_double_letter = np.array([116, 69, 133])
    # color_triple_word = np.array([29, 166, 204])
    # color_double_word = np.array([21, 133, 255])
    # color_field = np.array([97, 145, 156])

    FIELD_COLOR = ([85, 120, 128], [115, 255, 255])

    TLETTER_COLOR = ([105, 50, 100], [180, 255, 255])
    DLETTER_COLOR = ([105, 50, 100], [180, 255, 255])

    TWORD_COLOR = ([10, 110, 100], [40, 255, 255])
    DWORD_COLOR = ([10, 110, 100], [40, 255, 255])
