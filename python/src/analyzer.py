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

from __future__ import annotations

import logging
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import imutils
import numpy as np
from cv2.typing import MatLike

from config import SCORES, config
from game_board.board import GRID_H, GRID_W, get_x_position, get_y_position
from scrabble import BoardType, Tile

ANALYZE_THREADS = 4
BLANK_PROP = 76
MAX_TILE_PROB = 99
MATCH_ROTATIONS = [0, -5, 5, -10, 10, -15, 15]
THRESHOLD_PROP_BOARD = 97
THRESHOLD_PROP_TILE = 86
THRESHOLD_UMLAUT_BONUS = 2
UMLAUTS = ('Ä', 'Ü', 'Ö')
ORD_A = ord('A')
DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BASE_IMG_DIR = Path(__file__).resolve().parent / 'game_board' / 'img'
PATH_TILES_IMAGES = {
    'de': BASE_IMG_DIR / 'default',
    'en': BASE_IMG_DIR / 'en',
    'fr': BASE_IMG_DIR / 'fr',
    'es': BASE_IMG_DIR / 'es',
}

logger = logging.getLogger()
tiles_templates: list[TileTemplate] = []


@dataclass(kw_only=True)
class TileTemplate:  # pylint: disable=too-few-public-methods
    """representation of a tile"""

    name: str = 'Placeholder'
    img: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.uint8))


def load_tiles_templates() -> list[TileTemplate]:
    """load tile images from disk"""
    tiles_templates.clear()
    filepath = PATH_TILES_IMAGES[config.board.language]

    tile_list = sorted(SCORES[config.board.language], key=lambda t: SCORES[config.board.language][t], reverse=True)
    tile_list.remove('_')  # ohne Blanko-Stein

    for tile_name in tile_list:
        image_path = filepath / f'{tile_name}.png'
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            logger.error(f'load_tiles_templates: cannot read image: {image_path}')
            continue
        try:
            new_tile = TileTemplate(name=tile_name, img=image.astype(np.uint8))  # type: ignore
        except Exception:
            logger.exception('load_tiles_templates: failed processing image %s for tile %s', image_path, tile_name)
            continue
        tiles_templates.append(new_tile)
    return tiles_templates


def filter_candidates(
    coord: tuple[int, int], candidates: set[tuple[int, int]], ignore_set: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    """allow only valid field for analysis"""
    candidates = candidates.copy()
    result = set()
    stack = [coord]
    while stack:
        coordinates = stack.pop()
        if coordinates in candidates:
            candidates.remove(coordinates)
            if coordinates not in ignore_set:
                result.add(coordinates)
            stack.extend([(coordinates[0] + dx, coordinates[1] + dy) for dx, dy in DIRECTIONS])
    logger.debug(f'{result}')
    return result


def analyze_chunk(warped_gray: MatLike, board: BoardType, coord_list: set[tuple[int, int]]) -> BoardType:
    """find tiles on board"""

    def match_tile(img: MatLike, suggest_tile: str, suggest_prop: int) -> Tile:
        for _tile in tiles_templates:
            res = cv2.matchTemplate(img, _tile.img, cv2.TM_CCOEFF_NORMED)
            _, thresh, _, _ = cv2.minMaxLoc(res)
            thresh = int(thresh * 100)
            if _tile.name in UMLAUTS and thresh > suggest_prop - THRESHOLD_UMLAUT_BONUS:
                thresh = min(MAX_TILE_PROB, thresh + THRESHOLD_UMLAUT_BONUS)  # 2% Bonus for umlauts
                logger.debug(f'{chr(ORD_A + row)}{col + 1:2} => ({_tile.name},{thresh}) increased prop')
            if thresh > suggest_prop:
                suggest_tile, suggest_prop = _tile.name, thresh
        return Tile(letter=suggest_tile, prob=suggest_prop)

    def find_tile(gray: MatLike, tile: Tile) -> Tile:
        if tile.prob > THRESHOLD_PROP_BOARD:
            logger.debug(f'{chr(ORD_A + row)}{col + 1:2}: {tile} ({tile.prob}) tile on board prop > {THRESHOLD_PROP_BOARD} ')
            return tile

        for angle in MATCH_ROTATIONS:
            tile = match_tile(imutils.rotate(gray, angle), tile.letter, tile.prob)
            if tile.prob >= config.board.min_tiles_rate:
                break

        return tile if tile is not None and tile.prob > THRESHOLD_PROP_TILE else Tile('_', BLANK_PROP)

    try:
        for coord in coord_list:
            (col, row) = coord
            x, y = get_x_position(col), get_y_position(row)
            segment = warped_gray[y - 15 : y + GRID_H + 15, x - 15 : x + GRID_W + 15]
            board[coord] = find_tile(segment, board.get(coord, Tile('_', BLANK_PROP)))
            logger.info(f'{chr(ORD_A + row)}{col + 1:2}: {board[coord]}) found')
    except Exception:
        logger.exception(f'analyze_chunk failed for coords={coord_list}')
    return board


def analyze(warped_gray: MatLike, board: BoardType, candidates: set[tuple[int, int]]) -> BoardType:
    """start threads for analyze"""

    def chunkify(lst, chunks):
        return [lst[i::chunks] for i in range(chunks)]

    chunks = chunkify(list(candidates), ANALYZE_THREADS)  # chunks for picture analysis
    analyze_futures = []
    with ThreadPoolExecutor(max_workers=ANALYZE_THREADS, thread_name_prefix='analyze') as executor:
        for i in range(ANALYZE_THREADS):
            board_chunk = {key: board[key] for key in chunks[i] if key in board}
            analyze_futures.append(executor.submit(analyze_chunk, warped_gray, board_chunk, set(chunks[i])))
        done, not_done = futures.wait(analyze_futures)  # blocking wait
        for f in done:
            try:
                board.update(f.result())
            except Exception:  # noqa: PERF203 # `try`-`except` within a loop incurs performance overhead
                logger.exception('analyze future failed')
        for f in not_done:
            logger.error(f'analyze future not finished: {f}')
    return board


load_tiles_templates()
