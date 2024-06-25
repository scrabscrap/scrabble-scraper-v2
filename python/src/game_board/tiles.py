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

from typing import List

import cv2
import numpy as np

from config import config


class OneTile:  # pylint: disable=too-few-public-methods
    """representation of a tile"""

    def __init__(self):
        self.name = 'Placeholder'
        self.img = np.array([], dtype=np.uint8)
        self.w = 0
        self.h = 0


bag = config.tiles_bag
bag_as_list: List = sum(([k] * bag[k] for k in bag), [])
tiles: List[OneTile] = []


def scores(tile: str) -> int:
    """returns 0 if  '_' or lower chars otherwise the scoring value"""
    return 0 if tile.islower() or tile == '_' else config.tiles_scores[tile]


def load_tiles() -> List[OneTile]:
    """load tile images from disk"""

    tiles.clear()
    filepath = config.tiles_image_path
    tile_list = [*config.tiles_scores]
    tile_list.remove('_')  # without blank
    for tile_name in tile_list:
        image = cv2.imread(f'{filepath}/{tile_name}.png')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bitwise_not(gray)
        new_tile = OneTile()
        new_tile.name = tile_name
        new_tile.img = gray
        new_tile.w, new_tile.h = new_tile.img.shape[::-1]
        tiles.append(new_tile)
    return tiles


load_tiles()
