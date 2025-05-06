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

import os
from typing import List

import cv2
import numpy as np

from config import config

# fmt: off
SCORES = {
    'de': { 'A': 1, 'B': 3, 'C': 4, 'D': 1, 'E': 1, 'F': 4, 'G': 2, 'H': 2,
            'I': 1, 'J': 6, 'K': 4, 'L': 2, 'M': 3, 'N': 1, 'O': 2, 'P': 4,
            'Q': 10,'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 6, 'W': 3, 'X': 8,
            'Y': 10, 'Z': 3, '\u00c4': 6, '\u00d6': 8, '\u00dc': 6, '_': 0,
    },
    'en': { 'A': 1, 'B': 3, 'C': 4, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4,
            'I': 1, 'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 2, 'P': 3,
            'Q': 10,'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8,
            'Y': 4, 'Z': 10, '_': 0,
    },
    'fr': { 'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4,
            'I': 1, 'J': 8, 'K': 10,'L': 1, 'M': 2, 'N': 1, 'O': 2, 'P': 3,
            'Q': 8, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 10,'X': 10,
            'Y': 10,'Z': 10,'_': 0,
    },
    'es': { 'A': 1, 'B': 3, 'C': 3,'CH': 5, 'D': 2, 'E': 1, 'F': 4, 'G': 2,
            'H': 4, 'I': 1, 'J': 8, 'L': 1,'LL': 8, 'M': 3, 'N': 1, '\u00d1': 8,
            'O': 1, 'P': 3, 'Q': 5, 'R': 1,'RR': 8, 'S': 1, 'T': 1, 'U': 1,
            'V': 4, 'X': 8, 'Y': 4, 'Z': 10,'_': 0,
    },
}

BAGS = {
    'de': { 'A': 5, 'B': 2, 'C': 2, 'D': 4, 'E': 15,'F': 2, 'G': 3, 'H': 4,
            'I': 6, 'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 9, 'O': 3, 'P': 1,
            'Q': 1, 'R': 6, 'S': 7, 'T': 6, 'U': 6, 'V': 1, 'W': 1, 'X': 1,
            'Y': 1, 'Z': 1, '\u00c4': 1, '\u00d6': 1, '\u00dc': 1, '_': 2,
    },
    'en': { 'A': 9, 'B': 2, 'C': 2, 'D': 4, 'E': 12,'F': 2, 'G': 3, 'H': 2,
            'I': 9, 'J': 1, 'K': 1, 'L': 4, 'M': 2, 'N': 6, 'O': 8, 'P': 2,
            'Q': 1, 'R': 6, 'S': 4, 'T': 6, 'U': 4, 'V': 2, 'W': 2, 'X': 1,
            'Y': 2, 'Z': 1, '_': 2,
    },
    'fr': { 'A': 9, 'B': 2, 'C': 2, 'D': 3, 'E': 15,'F': 2, 'G': 2, 'H': 2,
            'I': 8, 'J': 1, 'K': 1, 'L': 5, 'M': 3, 'N': 6, 'O': 6, 'P': 2,
            'Q': 1, 'R': 6, 'S': 6, 'T': 6, 'U': 6, 'V': 2, 'W': 1, 'X': 1,
            'Y': 1, 'Z': 1, '_': 2,
    },
    'es': { 'A': 12,'B': 2, 'C': 4,'CH': 1, 'D': 5, 'E': 12,'F': 1, 'G': 2,
            'H': 2, 'I': 6, 'J': 1, 'L': 4,'LL': 1, 'M': 2, 'N': 5,'\u00d1': 1,
            'O': 9, 'P': 2, 'Q': 1, 'R': 5,'RR': 1, 'S': 6, 'T': 4, 'U': 5,
            'V': 1, 'X': 1, 'Y': 1, 'Z': 1, '_': 2,
    },
}
PATH_TILES_IMAGES = {
    'de': f'{os.path.dirname(__file__)}/img/default',
    'en': f'{os.path.dirname(__file__)}/img/en',
    'fr': f'{os.path.dirname(__file__)}/img/fr',
    'es': f'{os.path.dirname(__file__)}/img/es',
}
# fmt: on


class OneTile:  # pylint: disable=too-few-public-methods
    """representation of a tile"""

    def __init__(self):
        self.name = 'Placeholder'
        self.img = np.array([], dtype=np.uint8)


bag = BAGS[config.tiles_language]
bag_as_list = [k for k, count in bag.items() for _ in range(count)]
tiles: List[OneTile] = []


def scores(tile: str) -> int:
    """returns 0 if  '_' or lower chars otherwise the scoring value"""
    return 0 if tile.islower() or tile == '_' else SCORES[config.tiles_language][tile]


def load_tiles() -> List[OneTile]:
    """load tile images from disk"""

    tiles.clear()
    filepath = PATH_TILES_IMAGES[config.tiles_language]
    # tile_list = [*SCORES[config.board_language]]
    tile_list = sorted(SCORES[config.tiles_language], key=lambda t: SCORES[config.tiles_language][t], reverse=True)
    tile_list.remove('_')  # without blank
    for tile_name in tile_list:
        image = cv2.imread(f'{filepath}/{tile_name}.png', cv2.IMREAD_GRAYSCALE)
        new_tile = OneTile()
        new_tile.name = tile_name
        new_tile.img = image.astype(np.uint8)
        tiles.append(new_tile)
    return tiles


load_tiles()
