"""
 This file is part of the scrabble-scraper distribution (https://github.com/scrabscrap/scrabble-scraper)
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
import logging
import time
from concurrent import futures
from concurrent.futures import Future
from typing import Optional, Tuple

import cv2
import imutils
import numpy as np

from board.board import GRID_H, GRID_W, get_x_position, get_y_position
from board.tiles import tiles
from classic import Classic
from config import config
from custom import Custom
from scrab import Game
from threadpool import pool

Mat = np.ndarray[int, np.dtype[np.generic]]


def warp_image(img: Mat) -> Mat:
    """Delegates the warp of the ``img`` according to the configured board style"""
    if config.WARP and config.BOARD_LAYOUT == 'custom':
        return Custom.warp(img)
    elif config.WARP and config.BOARD_LAYOUT == 'classic':
        return Classic.warp(img)
    return img


def filter_image(img: Mat) -> tuple[Optional[Mat], set]:
    """Delegates the image filter of the ``img`` according to the configured board style"""
    if config.BOARD_LAYOUT == 'custom':
        return Custom.filter_image(img)
    elif config.BOARD_LAYOUT == 'classic':
        return Classic.filter_image(img)
    return None, set()


def filter_candidates(coord: tuple[int, int], candidates: set[tuple[int, int]], ignore_set: set[tuple[int, int]]) -> set:
    (col, row) = coord
    if coord not in candidates:  # already visited
        return set()
    candidates.remove(coord)
    result = set()
    # TODO: threshold for already recognized tiles
    if coord not in ignore_set:
        result.add(coord)
    result.add(filter_candidates((col + 1, row), candidates, ignore_set))
    result.add(filter_candidates((col - 1, row), candidates, ignore_set))
    result.add(filter_candidates((col, row + 1), candidates, ignore_set))
    result.add(filter_candidates((col, row - 1), candidates, ignore_set))
    return result


def analyze(warped_gray: Mat, board: dict, coord_list: set[tuple[int, int]]) -> dict:
    def match(img: Mat, suggest_tile: str, suggest_prop: int) -> tuple[str, int]:
        for _tile in tiles:
            res = cv2.matchTemplate(img, _tile.img, cv2.TM_CCOEFF_NORMED)  # type: ignore
            _, thresh, _, _ = cv2.minMaxLoc(res)
            if thresh > (suggest_prop / 100):
                suggest_tile = _tile.name
                suggest_prop = int(thresh * 100)
        return suggest_tile, suggest_prop

    def find_tile(coord: tuple[int, int], gray: Mat, _board: dict):
        (col, row) = coord
        tile, prop = _board[coord] if coord in _board else '_', 76
        if prop > 90:
            logging.debug(f"{chr(ord('A') + row)}{col + 1:2}: tile on board prop > 90 {tile} ({prop})")
            return _board[coord]
        tile, prop = match(gray, tile, prop)
        if prop < 90:
            tile, prop = match(imutils.rotate(gray, -10), tile, prop)
        if prop < 90:
            tile, prop = match(imutils.rotate(gray, 10), tile, prop)
        _board[coord] = (tile, prop) if tile is not None else ('_', 76)
        return _board[coord]

    for coord in coord_list:
        (col, row) = coord
        _y = get_y_position(row)
        _x = get_x_position(col)
        gray = warped_gray[_y - 15:_y + GRID_H + 15, _x - 15:_x + GRID_W + 15]
        tile, prop = find_tile(coord, gray, board)
        logging.debug(f"{chr(ord('A') + row)}{col + 1:2}: {tile} ({prop:2}) found")
    return board


def move(waitfor: Optional[Future], game: Game, img: Mat, player: int, played_time: Tuple[int, int]):
    """Process a move

    Args:
        waitfor (futures): wait for jobs to complete
        game(Game): the current game data
        img: the image to analyze
        player (int): active player
        played_time (int, int): current player times
    """
    logging.debug('move entry')

    #  1. warped = warp_image(img)
    #  2. warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    #  3. filtered, tiles_candidates = filter_image(image, board_layout)
    #  4. filtered_candidates = filter_candidates(tiles_candidates, game)
    #  5. splitted_list = np.array_split(filtered_candidates.toList(),3)
    #  6. board = game.current_board.copy()
    #  7. future1 = threadpool.submit(analyze_image, warped_gray, board, splitted_list[0] )
    #  8. future2 = threadpool.submit(analyze_image, warped_gray, board, splitted_list[1] )
    #  9. result3 = analyze_image(warped_gray, board, splitted_list[2])
    # 10. done, not_done = futures.waitfor({future1, furture2})
    # 11. move = calculate_move(board, game)
    # 12. store_move(move)
    # 13. game.add(move)
    # (14. Ftp.upload_move(move) -> im sep. thread damit die Nachfolge-Analyse nicht blockiert wird )

    # todo: check why this solution is not correct?
    # if waitfor is not None:
    #     done, not_done = futures.wait({waitfor})
    #     assert len(done) == 0, 'error on wait to future'
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)

    warped = warp_image(img)  # warp image if necessary
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)  # grayscale image
    filtered, tiles_candidates = filter_image(warped)  # find potential tiles on board
    if len(game.moves) > 3:  # ignore all tiles which are older than 3 moves
        ignore_coords = set(game.moves[-3].board.keys())
    else:
        ignore_coords = set()
    filtered_candidates = filter_candidates((7, 7), tiles_candidates.copy(), ignore_coords)
    board = game.moves[-1].board.copy() if len(game.moves) > 1 else {}  # get previous board

    # 3 threads for picture analysis
    splitted_list = np.array_split(list(filtered_candidates), 3)
    future1 = pool.submit(analyze, warped_gray, board, set(splitted_list[0]))  # 1. thread
    future2 = pool.submit(analyze, warped_gray, board, set(splitted_list[1]))  # 2. thread
    analyze(warped_gray, board, set(splitted_list[2]))  # 3. (this) thread
    done, _ = futures.wait({future1, future2})   # blocking wait
    assert len(done) == 2, 'error on wait to futures'

    # find new / removed tiles
    # move = Move()
    # game.add_move(move)
    # move = calculate_move(board, game)
    # store_move(move)
    # game.add(move)
    # return True
    logging.debug('move exit')


def valid_challenge(waitfor: Optional[Future], game: Game, player: int, played_time: Tuple[int, int]):
    """Process a valid challenge

    Args:
        waitfor (futures): wait for jobs to complete
        game(Game): the current game data
        player (int): active player
        played_time (int, int): current player times
    """
    logging.debug('valid_challenge entry')
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    game.add_valid_challenge(player, played_time)
    logging.debug('valid_challenge exit')


def invalid_challenge(waitfor: Optional[Future], game: Game, player: int, played_time: Tuple[int, int]):
    """Process an invalid challenge

    Args:
        waitfor (futures): wait for jobs to complete
        game(Game): the current game data
        player (int): active player
        played_time (int, int): current player times
    """
    logging.debug('invalid_challenge entry')
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    game.add_invalid_challenge(player, played_time)
    logging.debug('invalid_challenge exit')


def end_of_game(waitfor: Optional[Future]):
    logging.debug('end_of_game entry')
    # 1. filename = create_zip_from_game(game)
    # 2. Ftp.upload_game(filename)
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    time.sleep(1.5)
    logging.debug('end_of_games exit')
