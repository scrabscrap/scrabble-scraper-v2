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
# pylint: disable=too-many-lines

import copy
import logging
import time
from concurrent import futures
from concurrent.futures import Future
from datetime import datetime
from typing import List, Optional, Tuple

import cv2
import imutils
import numpy as np
from cv2.typing import MatLike

from classicboard import ClassicBoard
from config import config
from custom2012board import Custom2012Board
from custom2012kmeans import Custom2012kBoard
from custom2012pil import Custom2012PILBoard
from custom2020board import Custom2020Board
from custom2020pil import Custom2020PILBoard
from customboard import CustomBoard
from game_board.board import GRID_H, GRID_W, get_x_position, get_y_position
from game_board.tiles import tiles
from scrabble import Game, InvalidMoveExeption, Move, MoveType, NoMoveException
from threadpool import pool
from upload import upload
from util import TWarp, runtime_measure, trace


def get_last_warp() -> Optional[TWarp]:  # pylint: disable=too-many-return-statements
    """Delegates the warp of the ``img`` according to the configured board style"""
    if config.board_layout == 'classic':
        return ClassicBoard.last_warp
    if config.board_layout == 'custom2012':
        return Custom2012Board.last_warp
    if config.board_layout == 'custom2012kmeans':
        return Custom2012kBoard.last_warp
    if config.board_layout == 'custom2012pil':
        return Custom2012PILBoard.last_warp
    if config.board_layout == 'custom2020':
        return Custom2020Board.last_warp
    if config.board_layout == 'custom2020pil':
        return Custom2020PILBoard.last_warp
    return CustomBoard.last_warp


def clear_last_warp():
    """Delegates the warp of the ``img`` according to the configured board style"""
    if config.board_layout == 'classic':
        ClassicBoard.last_warp = None
    elif config.board_layout == 'custom2012':
        Custom2012Board.last_warp = None
    elif config.board_layout == 'custom2012kmeans':
        Custom2012kBoard.last_warp = None
    elif config.board_layout == 'custom2012pil':
        Custom2012PILBoard.last_warp = None
    elif config.board_layout == 'custom2020':
        Custom2020Board.last_warp = None
    elif config.board_layout == 'custom2020pil':
        Custom2020PILBoard.last_warp = None
    CustomBoard.last_warp = None


@runtime_measure
def warp_image(img: MatLike) -> tuple[MatLike, MatLike]:
    """Delegates the warp of the ``img`` according to the configured board style"""
    logging.debug(f'({config.board_layout})')
    warped = img
    if config.video_warp:
        if config.board_layout == 'classic':
            warped = ClassicBoard.warp(img)
        elif config.board_layout == 'custom2012':
            warped = Custom2012Board.warp(img)
        elif config.board_layout == 'custom2012kmeans':
            warped = Custom2012kBoard.warp(img)
        elif config.board_layout == 'custom2012pil':
            warped = Custom2012PILBoard.warp(img)
        elif config.board_layout == 'custom2020':
            warped = Custom2020Board.warp(img)
        elif config.board_layout == 'custom2020pil':
            warped = Custom2020PILBoard.warp(img)
        else:
            warped = CustomBoard.warp(img)
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    return warped, warped_gray


@runtime_measure
def filter_image(img: MatLike) -> tuple[Optional[MatLike], set]:  # pylint: disable=too-many-return-statements
    """Delegates the image filter of the ``img`` according to the configured board style"""
    logging.debug(f'({config.board_layout})')
    if config.board_layout == 'classic':
        return ClassicBoard.filter_image(img)
    if config.board_layout == 'custom2012':
        return Custom2012Board.filter_image(img)
    if config.board_layout == 'custom2012kmeans':
        return Custom2012kBoard.filter_image(img)
    if config.board_layout == 'custom2012pil':
        return Custom2012PILBoard.filter_image(img)
    if config.board_layout == 'custom2020':
        return Custom2020Board.filter_image(img)
    if config.board_layout == 'custom2020pil':
        return Custom2020PILBoard.filter_image(img)
    return CustomBoard.filter_image(img)


def filter_candidates(coord: tuple[int, int], candidates: set[tuple[int, int]], ignore_set: set[tuple[int, int]]) -> set:
    """allow only valid field for analysis"""
    (col, row) = coord
    result: set = set()
    if coord not in candidates:  # already visited
        return result
    candidates.remove(coord)
    if coord not in ignore_set:
        result.add(coord)
    result = result | filter_candidates((col + 1, row), candidates, ignore_set)
    result = result | filter_candidates((col - 1, row), candidates, ignore_set)
    result = result | filter_candidates((col, row + 1), candidates, ignore_set)
    result = result | filter_candidates((col, row - 1), candidates, ignore_set)
    return result


def analyze(warped_gray: MatLike, board: dict, coord_list: set[tuple[int, int]]) -> dict:
    """find tiles on board"""

    def match(img: MatLike, suggest_tile: str, suggest_prop: int) -> tuple[str, int]:
        for _tile in tiles:
            res = cv2.matchTemplate(img, _tile.img, cv2.TM_CCOEFF_NORMED)
            _, thresh, _, _ = cv2.minMaxLoc(res)
            thresh = int(thresh * 100)
            if _tile.name in ('Ä', 'Ü', 'Ö') and thresh >= suggest_prop - 1:
                logging.debug(f"{chr(ord('A') + row)}{col + 1:2} => ({_tile.name},{thresh}) increase prop to {thresh+2}")
                thresh = min(99, thresh + 5)  # 5% Bonus for umlauts
            if thresh > suggest_prop:
                suggest_tile = _tile.name
                suggest_prop = thresh
        return suggest_tile, suggest_prop

    def find_tile():
        (tile, prop) = board.get(coord, ('_', 76))
        if prop >= 90:
            logging.debug(f"{chr(ord('A') + row)}{col + 1:2}: {tile} ({prop}) tile on board prop >= 90 ")
            return board[coord]
        (tile, prop) = match(gray, tile, prop)
        if prop < 90:
            (tile, prop) = match(imutils.rotate(gray, -10), tile, prop)
        if prop < 90:
            (tile, prop) = match(imutils.rotate(gray, 10), tile, prop)
        if prop < 90 and tile != '_':
            (tile, prop) = match(imutils.rotate(gray, -5), tile, prop)
        if prop < 90 and tile != '_':
            (tile, prop) = match(imutils.rotate(gray, 5), tile, prop)
        if prop < 90 and tile != '_':
            (tile, prop) = match(imutils.rotate(gray, -15), tile, prop)
        if prop < 90 and tile != '_':
            (tile, prop) = match(imutils.rotate(gray, 15), tile, prop)
        board[coord] = (tile, prop) if tile is not None else ('_', 76)
        return board[coord]

    for coord in coord_list:
        (col, row) = coord
        _y = get_y_position(row)
        _x = get_x_position(col)
        gray = warped_gray[_y - 15 : _y + GRID_H + 15, _x - 15 : _x + GRID_W + 15]
        new_tile, new_prop = find_tile()
        logging.info(f"{chr(ord('A') + row)}{col + 1:2}: {new_tile} ({new_prop:2}) found")
    return board


def remove_blanko(waitfor: Optional[Future], game: Game, coord: str, event=None):
    """remove blank

    Args:
    game(Move): the game to fix
    coord: coord of blank
    event: event to inform webservice
    """
    if waitfor is not None:  # wait for previous moves
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'

    dirty: bool = False
    logging.info(f'remove blanko {coord}')
    for mov in game.moves:
        board = mov.board
        _, col, row = mov.calc_coord(coord)
        if (col, row) in board and (board[(col, row)][0] == '_' or board[(col, row)][0].islower()):
            if (col, row) in mov.new_tiles:
                dirty = True
                del mov.new_tiles[(col, row)]
            if dirty:
                del mov.board[(col, row)]
                mov.is_vertical, mov.coord, mov.word = _find_word(mov.board, sorted(mov.new_tiles))
                mov.type = MoveType.REGULAR
                prev_score = game.moves[mov.move - 2].score if mov.move > 2 else (0, 0)
                mov.points, mov.score, mov.is_scrabble = mov.calculate_score(prev_score)
                # store move
                _store(game, mov)

    if event and not event.is_set():
        event.set()


def set_blankos(waitfor: Optional[Future], game: Game, coord: str, value: str, event=None):
    """set char for blanko

    Args:
    game(Move): the game to fix
    coord: coord of blank
    value: char for blank
    event: event to inform webservice
    """
    if waitfor is not None:  # wait for previous moves
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'

    logging.info(f'set blanko {coord} to {value}')
    for mov in game.moves:
        board = mov.board
        _, col, row = mov.calc_coord(coord)
        if (col, row) in board and (board[(col, row)][0] == '_' or board[(col, row)][0].islower()):
            board[(col, row)] = (value, board[(col, row)][1])
            if (col, row) in mov.new_tiles:
                mov.new_tiles[(col, row)] = value
                index = row - mov.coord[1] if mov.is_vertical else col - mov.coord[0]
                mov.word = f'{mov.word[:index]}{value}{mov.word[index + 1:]}'
    if event and not event.is_set():
        event.set()


def admin_insert_moves(waitfor: Optional[Future], game: Game, move_number: int, event=None):  # pylint: disable=too-many-locals
    """insert two exchange moves before move number"""
    if waitfor is not None:  # wait for previous moves
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'

    if 0 < move_number <= len(game.moves):
        logging.info(f'insert before move {move_number}')
        assert game.moves[move_number - 1].move == move_number

        index = move_number - 1
        player1 = game.moves[index].player
        player2 = 0 if player1 == 1 else 1
        board = game.moves[index - 1].board.copy() if index > 0 else {}
        played_time = game.moves[index - 1].played_time if index > 0 else (0, 0)
        previous_score = game.moves[index - 1].score if index > 0 else (0, 0)
        img = game.moves[index].img.copy() if game.moves[index].img is not None else None  # type: ignore[attr-defined]

        move1 = Move(
            MoveType.EXCHANGE,
            player=player1,
            coord=(0, 0),
            is_vertical=True,
            word='',
            new_tiles={},
            removed_tiles={},
            board=board,
            played_time=played_time,
            previous_score=previous_score,
            img=img,
        )
        move2 = Move(
            MoveType.EXCHANGE,
            player=player2,
            coord=(0, 0),
            is_vertical=True,
            word='',
            new_tiles={},
            removed_tiles={},
            board=board,
            played_time=played_time,
            previous_score=previous_score,
            img=img,
        )

        game.moves.insert(index, move2)
        game.moves.insert(index, move1)

        for i, mov in enumerate(game.moves[index:]):
            mov.move = i + index + 1
            logging.debug(f'set/store move index {index + i} / move number {mov.move}')
            _store(game, mov)
        if event and not event.is_set():
            event.set()
    else:
        logging.warning(f'wrong move number for insert after move: {move_number}')
        raise ValueError('invalid move number')


def admin_change_score(waitfor: Optional[Future], game: Game, move_number: int, score: Tuple[int, int], event=None):
    """fix scores (direct call from admin)

    Args:
    game(Move): the game to fix
    move_number: the move to fix(beginning with 1)
    score(Tuple[int, int]): new score
    event: event to inform webservice
    """
    if waitfor is not None:  # wait for previous moves
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'

    if 0 < move_number <= len(game.moves):
        mov = game.moves[move_number - 1]
        assert mov.move == move_number

        delta = tuple(np.subtract(mov.score, score))
        if delta[0] != 0 or delta[1] != 0:
            mov.modification_cache['score'] = mov.score
        logging.debug(f'set score for move {move_number} {mov.score} => {score} / delta {delta}')
        for mov in game.moves[move_number - 1 :]:
            mov.score = (int(mov.score[0] - delta[0]), int(mov.score[1] - delta[1]))
            logging.info(f'>> move {mov.move}: {mov.score}')
            _store(game, mov, with_image=False)
        if event and not event.is_set():
            event.set()
    else:
        logging.warning(f'wrong move number for change score: {move_number}')
        raise ValueError('invalid move number')


def admin_change_move(
    waitfor: Optional[Future], game: Game, move_number: int, coord: Tuple[int, int], isvertical: bool, word: str, event=None
):
    # pylint: disable=too-many-arguments, too-many-locals,too-many-branches,too-many-statements, too-many-positional-arguments
    """fix move(direct call from admin)

    The provided tiles(word) will be set on the board with a probability of 99%

    Args:
        waitfor: flag for running tasks
        game(Move): the game to fix
        move_number: the move to fix(beginning with 1)
        coord: coordinates on board(0 <= col < 15, 0 <= row < 15)
        isvertical: if this corrected move is vertical
        word: the new word valid chars(A - Z._) crossing chars will replaced with '.'
        event: event to infom webservice
    """
    if waitfor is not None:  # wait for previous moves
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'

    moves = game.moves
    if move_number < 1 or move_number > len(game.moves):
        raise ValueError('invalid move number ({move_number=})')

    assert moves[move_number - 1].move == move_number
    assert 0 <= coord[0] < 15
    assert 0 <= coord[1] < 15

    index = move_number - 1

    logging.debug(f'try to fix move {move_number} at {coord} vertical={isvertical} with {word}')
    board = moves[index].board.copy()

    tiles_to_remove = moves[index].new_tiles.copy()  # tiles to delete
    for elem in tiles_to_remove:
        del board[elem]  # remove tiles on board from incorrect move
    logging.debug(f'tiles_to_remove {tiles_to_remove}')
    tiles_to_add: dict = {}  # tiles to add
    (col, row) = coord
    new_word = ''
    for i, char in enumerate(word):
        (xcol, xrow) = (col, row + i) if isvertical else (col + i, row)
        if (xcol, xrow) in board:
            new_word += '.'
        else:
            new_word += char
            tiles_to_add[(xcol, xrow)] = (char, 99)
    word = new_word
    logging.debug(f'tiles_to_add {tiles_to_add} / word {word}')
    if tiles_to_remove or tiles_to_add:
        game.moves[index].modification_cache['coord'] = coord
        game.moves[index].modification_cache['isvertical'] = isvertical
        game.moves[index].modification_cache['word'] = word

    previous_board = game.moves[index - 1].board if move_number > 1 else {}
    previous_score = game.moves[index - 1].score if move_number > 1 else (0, 0)

    admin_recalc_moves(game, index, tiles_to_remove, tiles_to_add, previous_board, previous_score)
    for i in range(index, len(game.moves)):
        _store(game, game.moves[i], with_image=False)

    if event and not event.is_set():
        event.set()


def admin_recalc_moves(
    game: Game, index: int, tiles_to_remove: dict, tiles_to_add: dict, previous_board: dict, previous_score: Tuple[int, int]
):  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """recalculate move scores and points after admin changes"""
    moves = game.moves
    for i in range(index, len(moves)):
        new_move = copy.deepcopy(moves[i])  # board, img, score

        for elem in tiles_to_remove:  # repair board
            if elem in new_move.board and new_move.board[elem] == tiles_to_remove[elem]:
                del new_move.board[elem]
        new_move.board |= tiles_to_add

        if new_move.type == MoveType.CHALLENGE_BONUS and new_move.player == 0:
            new_move.score = (previous_score[0] - config.malus_doubt, previous_score[1])
        elif new_move.type == MoveType.CHALLENGE_BONUS and new_move.player == 1:
            new_move.score = (previous_score[0], previous_score[1] - config.malus_doubt)
        elif new_move.type == MoveType.WITHDRAW:
            if len(moves) > 1:
                new_move.points = -moves[i - 1].points
                new_move.word = moves[i - 1].word
                new_move.removed_tiles = moves[i - 1].new_tiles
                new_move.new_tiles = {}
        else:
            save_cache = new_move.modification_cache
            new_move = _move_processing(
                game, new_move.player, new_move.played_time, new_move.img, new_move.board, previous_board, previous_score
            )
            new_move.modification_cache = save_cache
        new_move.move = i + 1
        previous_board = new_move.board
        previous_score = new_move.score
        moves[i] = new_move
        logging.info(
            f'recalculate move #{moves[i].move} ({moves[i].type}) new points {moves[i].points} new score {moves[i].score}'
        )
        logging.info(f'\n{game.board_str(i)}')


def admin_del_challenge(waitfor: Optional[Future], game: Game, move_number: int, event=None):
    """delete challenge move number"""
    if waitfor is not None:  # wait for running actions
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'
    if move_number < 1 or move_number > len(game.moves):
        raise ValueError(f'invalid move number for delete challenge {move_number=}')

    index = move_number - 1
    assert game.moves[index].move == move_number, 'Invalid move_number'

    if game.moves[index].type not in (MoveType.WITHDRAW, MoveType.CHALLENGE_BONUS):
        raise ValueError(f'invalid move type (type={game.moves[index].type})')

    logging.debug(f'delete {move_number=} ({index=})')
    to_delete = game.moves.pop(index)  ## move number anpassen !
    for i in range(index, len(game.moves)):
        game.moves[i].move -= 1
    previous_board = game.moves[index - 1].board if move_number > 1 else {}
    previous_score = game.moves[index - 1].score if move_number > 1 else (0, 0)
    tiles_to_add = {}
    if to_delete.type == MoveType.WITHDRAW:
        tiles_to_add = game.moves[index - 1].new_tiles
    admin_recalc_moves(game, index, {}, tiles_to_add, previous_board, previous_score)
    for i in range(index, len(game.moves)):
        _store(game, game.moves[i], with_image=True)
    if event and not event.is_set():
        event.set()


def admin_toggle_challenge_type(waitfor: Optional[Future], game: Game, move_number: int, event=None):
    """toggle challenge type on move number"""
    if waitfor is not None:  # wait for running actions
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'
    if move_number < 1 or move_number > len(game.moves):
        raise ValueError(f'invalid move number ({move_number=})')

    index = move_number - 1
    assert game.moves[index].move == move_number, 'Invalid move_number'

    to_change = game.moves[index]
    if to_change.type not in (MoveType.WITHDRAW, MoveType.CHALLENGE_BONUS):
        raise ValueError(f'invalid move type (type={to_change.type})')

    previous_board = game.moves[index - 1].board if move_number > 1 else {}
    previous_score = game.moves[index - 1].score if move_number > 1 else (0, 0)
    if to_change.type == MoveType.WITHDRAW:  # new type=MoveType.CHALLENGE_BONUS
        to_change.type = MoveType.CHALLENGE_BONUS
        to_change.points = config.malus_doubt * -1
        to_change.word = ''
        to_change.removed_tiles = {}
    else:  # new type=MoveType.WITHDRAW
        to_change.type = MoveType.WITHDRAW
        to_change.points = -game.moves[index - 1].points
        to_change.word = game.moves[index - 1].word
        to_change.removed_tiles = game.moves[index - 1].new_tiles
    to_change.player = 0 if to_change.player == 1 else 1
    to_change.new_tiles = {}
    to_change.modification_cache = {}
    to_change.score = (
        (previous_score[0] + to_change.points, previous_score[1])
        if to_change.player == 0
        else (previous_score[0], previous_score[1] + to_change.points)
    )
    admin_recalc_moves(game, index, to_change.removed_tiles, {}, previous_board, previous_score)
    for i in range(index, len(game.moves)):
        _store(game, game.moves[i], with_image=True)
    if event and not event.is_set():
        event.set()


def admin_ins_challenge(waitfor: Optional[Future], game: Game, move_number: int, move_type: MoveType, event=None):
    """insert invalid challenge or withdraw for move number"""
    if waitfor is not None:  # wait for running actions
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'
    if move_number < 1 or move_number > len(game.moves):
        raise ValueError(f'invalid move number ({move_number=})')

    index = move_number - 1
    assert game.moves[index].move == move_number, 'Invalid move_number'

    logging.debug(f'insert challenge {move_type} for {move_number=}')
    to_insert = copy.deepcopy(game.moves[index])
    to_insert.move += 1
    to_insert.removed_tiles = {}
    if move_type == MoveType.CHALLENGE_BONUS:
        to_insert.type = MoveType.CHALLENGE_BONUS
        to_insert.points = config.malus_doubt * -1
        to_insert.word = ''
        to_insert.player = 0 if to_insert.player == 1 else 1
    else:
        to_insert.type = MoveType.WITHDRAW
        to_insert.points = to_insert.points * -1
        to_insert.removed_tiles = to_insert.new_tiles
    to_insert.new_tiles = {}
    to_insert.modification_cache = {}
    to_insert.score = (
        (to_insert.score[0] + to_insert.points, to_insert.score[1])
        if to_insert.player == 0
        else (to_insert.score[0], to_insert.score[1] + to_insert.points)
    )
    if index < len(game.moves):
        game.moves.insert(index + 1, to_insert)
    else:
        game.moves.append(to_insert)

    previous_board = game.moves[index - 1].board if index > 0 else {}
    previous_score = game.moves[index - 1].score if index > 0 else (0, 0)
    for i in range(index + 1, len(game.moves)):
        game.moves[i].move += 1
    admin_recalc_moves(game, index + 1, to_insert.removed_tiles, {}, previous_board, previous_score)
    for i in range(index, len(game.moves)):
        _store(game, game.moves[i], with_image=True)
    if event and not event.is_set():
        event.set()


@trace
def move(waitfor: Optional[Future], game: Game, img: MatLike, player: int, played_time: Tuple[int, int], event=None):
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    """Process a move

    Args:
        waitfor(futures): wait for jobs to complete
        game(Game): the current game data
        img: the image to analyze
        player(int): active player
        played_time(int, int): current player times
        event: event to set
    """
    warped, board = _image_processing(waitfor, game, img)

    previous_board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}  # get previous board information
    previous_score = game.moves[-1].score if len(game.moves) > 0 else (0, 0)

    current_move = _move_processing(game, player, played_time, warped, board, previous_board, previous_score)

    game.add_move(current_move)  # 9. add move
    if event and not event.is_set():
        event.set()

    logging.info(f'\n{game.board_str()}')
    if logging.getLogger('root').isEnabledFor(logging.DEBUG):
        msg = '\n' + ''.join(f'{mov.gcg_str(game.nicknames)}\n' for mov in game.moves)
        logging.debug(f'{msg}\nscores: {game.moves[-1].score}\napi: {game.json_str()}')
    _development_recording(game, img, suffix='~original')
    _development_recording(game, warped, suffix='~warped')
    _store(game, game.moves[-1])


@trace
def valid_challenge(waitfor: Optional[Future], game: Game, player: int, played_time: Tuple[int, int], event=None):
    """Process a valid challenge

    Args:
        waitfor(futures): wait for jobs to complete
        game(Game): the current game data
        player(int): active player
        played_time(int, int): current player times
        event: event to set
    """
    while waitfor is not None and waitfor.running():
        time.sleep(0.01)
    try:
        game.add_valid_challenge(player, played_time)
        if event and not event.is_set():
            event.set()

        logging.info(f'new scores {game.moves[-1].score}: {game.json_str()}\n{game.board_str()}')
        _store(game, game.moves[-1])
    except Exception as oops:  # pylint: disable=broad-exception-caught
        logging.error(f'exception on valid_challenge {oops}')
        logging.info('no new move')


@trace
def invalid_challenge(waitfor: Optional[Future], game: Game, player: int, played_time: Tuple[int, int], event=None):
    """Process an invalid challenge

    Args:
        waitfor(futures): wait for jobs to complete
        game(Game): the current game data
        player(int): active player
        played_time(int, int): current player times
        event: event to set
    """
    while waitfor is not None and waitfor.running():
        time.sleep(0.01)
    try:
        game.add_invalid_challenge(player, played_time)  # 9. add move
        if event and not event.is_set():
            event.set()

        logging.info(f'new scores {game.moves[-1].score}: {game.json_str()}\n{game.board_str()}')
        _store(game, game.moves[-1])
    except Exception as oops:  # pylint: disable=broad-exception-caught
        logging.error(f'exception on in_valid_challenge {oops}')
        logging.info('no new move')


@trace
def store_status(game: Game):
    """store current status.json - does not update data - *.json !"""
    _store(game, None)


@trace
def start_of_game(game: Game):
    """start of game"""
    import glob
    import os

    import util

    pool.submit(upload.delete_files)  # first delete images and data files on ftp server
    try:
        file_list = glob.glob(f'{config.web_dir}/image-*.jpg')
        for file_path in file_list:
            os.remove(file_path)
        file_list = glob.glob(f'{config.web_dir}/data-*.json')
        for file_path in file_list:
            os.remove(file_path)
        if file_list:
            util.rotate_logs()
    except OSError:
        logging.error('OS Error on delete web data/image files')
    _store(game, None)


@trace
def end_of_game(waitfor: Optional[Future], game: Game, event=None):
    # pragma: no cover #pylint: disable=too-many-locals # no ftp upload on tests
    """Process end of game

    Args:
        waitfor(futures): wait for jobs to complete
        game(Game): the current game data
        event: event to set
    """
    while waitfor is not None and waitfor.running():
        time.sleep(0.01)
    # time.sleep(1.5)
    if len(game.moves) > 0:
        points, rackstr = _end_of_game_calculate_rack(game)
        game.add_last_rack(points, rackstr)
        if event and not event.is_set():
            event.set()
        msg = '\n' + ''.join(f'{mov.gcg_str(game.nicknames)}\n' for mov in game.moves)
        logging.debug(f'last rack scores:\n{game.board_str()}{msg}\nscores: {game.moves[-1].score}\napi: {game.json_str()}')
        logging.info(game.dev_str())

        _store(game, game.moves[-2])
        _store(game, game.moves[-1])


def _end_of_game_calculate_rack(game: Game) -> Tuple[Tuple[int, int], str]:
    from game_board.tiles import bag_as_list, scores

    def calculate_bag(_mov) -> list[str]:
        values = [t for (t, _) in _mov.board.values()]
        result = bag_as_list.copy()
        for val in values:
            toremove = '_' if val.isalpha() and val.islower() else val
            if toremove in result:
                result.remove(toremove)
        return result

    bag_len = 0
    i = -1
    for i, mov in enumerate(reversed(game.moves)):
        bag = calculate_bag(mov)
        if len(bag) >= 14:
            bag_len = len(bag) - 14
            i = len(game.moves) - i - 1  # revert Index
            break
    else:
        i = -1  # if no moves found
    rack, prev_rack = [7, 7], [7, 7]
    prev_bag_len = bag_len
    for mov in game.moves[i + 1 :]:
        if mov.type == MoveType.WITHDRAW:
            rack[mov.player], bag_len = prev_rack[mov.player], prev_bag_len
            from_bag = 0
        else:
            prev_rack[mov.player], prev_bag_len = rack[mov.player], bag_len
            mov_len = len(mov.new_tiles)
            from_bag = min(mov_len, bag_len)
            rack[mov.player] -= mov_len - from_bag
            bag_len -= from_bag
        logging.info(f'move={mov.move} {mov.type} {mov.player=} rack-size={rack[mov.player]} {from_bag=} {bag_len=}')
    if len(game.moves) > 0:
        bag = calculate_bag(game.moves[-1])
        points = sum(scores(elem) for elem in bag)
        if rack[0] == 0 and rack[1] > 0:
            return (points, -points), ''.join(bag)
        if rack[1] == 0 and rack[0] > 0:
            return (-points, points), ''.join(bag)
    return (0, 0), '?'


def _changes(board: dict, previous_board: dict) -> Tuple[dict, dict, dict, dict]:
    for coord, (prev_value, prev_score) in previous_board.items():
        if coord in board and prev_score > board[coord][1]:
            logging.debug(f'use value from old board {coord}')
            board[coord] = (prev_value, prev_score)
    new_tiles = {i: board[i] for i in set(board.keys()).difference(previous_board)}
    removed_tiles = {i: previous_board[i] for i in set(previous_board.keys()).difference(board)}
    changed_tiles = {i: board[i] for i in previous_board if i not in removed_tiles and previous_board[i][0] != board[i][0]}
    return board, new_tiles, removed_tiles, changed_tiles


def _chunkify(lst, chunks):
    return [lst[i::chunks] for i in range(chunks)]


def _find_word(board: dict, changed: List) -> Tuple[bool, Tuple[int, int], str]:
    if len(changed) < 1:
        logging.info('move: no new tiles detected')
        raise NoMoveException('move: no new tiles')
    horizontal = len({col for col, _ in changed}) > 1
    vertical = len({row for _, row in changed}) > 1
    if vertical and horizontal:
        logging.warning(f'illegal move: {changed}')
        raise InvalidMoveExeption('move: illegal move horizontal and vertical changes detected')
    if len(changed) == 1:  # only 1 tile
        col, row = changed[-1]
        horizontal = ((col - 1, row) in board) or ((col + 1, row) in board)
        vertical = False if horizontal else ((col, row - 1) in board) or ((col, row + 1) in board)
    col, row = changed[0]
    min_col, min_row = col, row
    word = ''
    if vertical:
        while row > 0 and (col, row - 1) in board:
            row -= 1
        min_row = row
        while row < 15 and (col, row) in board:
            word += board[(col, row)][0] if (col, row) in changed else '.'
            row += 1
    else:
        while col > 0 and (col - 1, row) in board:
            col -= 1
        min_col = col
        while col < 15 and (col, row) in board:
            word += board[(col, row)][0] if (col, row) in changed else '.'
            col += 1
    return vertical, (min_col, min_row), word


@runtime_measure
def _image_processing(waitfor: Optional[Future], game: Game, img: MatLike) -> Tuple[MatLike, dict]:
    # pylint: disable=too-many-locals
    if waitfor is not None:  # wait for previous moves
        done, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'
    warped, warped_gray = warp_image(img)  # 1. warp image if necessary
    filtered_image, tiles_candidates = filter_image(warped)  # 3. find potential tiles on board
    _development_recording(game, filtered_image, suffix='~filter', is_next_move=True)

    if len(game.moves) > 1:  # 3a. check for wrong blank tiles
        to_del = [i for i in game.moves[-1].new_tiles if (game.moves[-1].board[i][0] == '_') and i not in tiles_candidates]  # noqa: W503 # pylint: disable=line-too-long
        if to_del:
            _move = game.moves[-1]
            for i in to_del:
                logging.warning(f'remove blank tiles from the last move because they are no longer recognized {i}')
                try:
                    del _move.new_tiles[i]
                    del _move.board[i]
                except KeyError:
                    pass  # already deleted
            logging.info(f'try to recalculate move #{_move.move}')
            try:
                _move.is_vertical, _move.coord, _move.word = _find_word(_move.board, sorted(_move.new_tiles))
                _move.type = MoveType.REGULAR
                prev_score = game.moves[-2].score if len(game.moves) > 2 else (0, 0)
                _move.points, _move.score, _move.is_scrabble = _move.calculate_score(prev_score)
                logging.warning(f'result correction move: {_move.gcg_str()}')
            except (NoMoveException, InvalidMoveExeption):
                logging.warning(f'could not correct move #{_move.move}')

    ignore_coords = set()
    if len(game.moves) > config.scrabble_verify_moves:
        # if opponents move has a valid challenge
        if game.moves[-1 * config.scrabble_verify_moves + 1].type in (MoveType.PASS_TURN, MoveType.EXCHANGE, MoveType.WITHDRAW):
            ignore_coords = set(
                {i: i for i in game.moves[-1 * config.scrabble_verify_moves + 1].board if i in game.moves[-1].board}
            )
        else:
            ignore_coords = set(
                {i: i for i in game.moves[-1 * config.scrabble_verify_moves].board if i in game.moves[-1].board}
            )
    tiles_candidates = tiles_candidates | ignore_coords  # tiles_candidates must contain ignored_coords
    filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
    logging.debug(f'filtered_candidates {filtered_candidates}')

    board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}  # copy board for analyze
    chunks = _chunkify(list(filtered_candidates), 3)  # 5. picture analysis
    future1 = pool.submit(analyze, warped_gray, board, set(chunks[0]))  # 1. thread
    future2 = pool.submit(analyze, warped_gray, board, set(chunks[1]))  # 2. thread
    analyze(warped_gray, board, set(chunks[2]))  # 3. (this) thread
    done, _ = futures.wait({future1, future2})  # 6. blocking wait
    assert len(done) == 2, 'error on wait to futures'
    return warped, board


def _move_processing(
    game: Game,
    player: int,
    played_time: Tuple[int, int],
    warped,
    board: dict,
    previous_board: dict,
    previous_score: Tuple[int, int],
) -> Move:
    # pylint: disable=too-many-locals, too-many-branches, too-many-arguments, too-many-positional-arguments

    def strip_invalid_blanks(current_board, new_tiles):
        blanks = {(col, row) for col, row in new_tiles if new_tiles[(col, row)][0] == '_'}
        if not blanks:  # no blanks; skip
            return current_board, new_tiles

        previous_tiles = new_tiles.copy()
        set_of_cols = {col for col, row in new_tiles if new_tiles[(col, row)][0] != '_'}  # cols tiles with character
        set_of_rows = {row for col, row in new_tiles if new_tiles[(col, row)][0] != '_'}  # rows tiles with character

        if len(set_of_rows) == 1 or len(set_of_cols) == 1:
            (min_col, max_col) = (min(set_of_cols), max(set_of_cols))
            (min_row, max_row) = (min(set_of_rows), max(set_of_rows))
            # either columns or rows
            logging.debug(f'{set_of_cols=} {set_of_rows=} {blanks=} {min_row=} {max_row=} {min_col=} {max_col=}')
            if len(set_of_cols) == 1 and len(set_of_rows) == 1:  # only one tile: remove all blanks not in the column/row
                new_tiles = {k: v for k, v in new_tiles.items() if k[0] in set_of_cols or k[1] in set_of_rows}
            elif len(set_of_cols) == 1:  # vertical: remove all blanks next to the column
                new_tiles = {k: v for k, v in new_tiles.items() if k[0] in set_of_cols}
            elif len(set_of_rows) == 1:  # horizontal: remove all blanks next to the row
                new_tiles = {k: v for k, v in new_tiles.items() if k[1] in set_of_rows}

            if len(set_of_cols) == 1:  # vertical: find path to min/max character
                for blank in (x for x in blanks if x[0] == min_col):
                    if any((blank[0], row) not in current_board for row in range(min_row, blank[1])):
                        del new_tiles[blank]
                    if any((blank[0], row) not in current_board for row in range(blank[1], max_row)):
                        del new_tiles[blank]

            if len(set_of_rows) == 1:  # horizontal: find path to min/max character
                for blank in (x for x in blanks if x[1] == min_row):
                    if any((col, blank[1]) not in current_board for col in range(min_col, blank[0])):
                        del new_tiles[blank]
                    if any((col, blank[1]) not in current_board for col in range(blank[0], max_col)):
                        del new_tiles[blank]

        removed_tiles = previous_tiles.keys() - new_tiles
        for k in removed_tiles:
            del current_board[k]
        if removed_tiles:
            logging.debug(f'new_tiles={previous_tiles} remaining {new_tiles=}')
        return current_board, new_tiles

    current_board, new_tiles, removed_tiles, changed_tiles = _changes(board, previous_board)  # find changes on board
    current_board, new_tiles = strip_invalid_blanks(current_board=current_board, new_tiles=new_tiles)

    if len(changed_tiles) > 0:  # 7. fix old moves
        previous_score = _recalculate_score_on_tiles_change(game, board, changed_tiles)
    try:  # 8. find word and create move
        is_vertical, coord, word = _find_word(current_board, sorted(new_tiles))
        current_move = Move(
            MoveType.REGULAR,
            player=player,
            coord=coord,
            is_vertical=is_vertical,
            word=word,
            new_tiles=new_tiles,
            removed_tiles=removed_tiles,
            board=current_board,
            played_time=played_time,
            previous_score=previous_score,
            img=warped,
        )
    except NoMoveException:
        current_move = Move(
            MoveType.EXCHANGE,
            player=player,
            coord=(0, 0),
            is_vertical=True,
            word='',
            new_tiles=new_tiles,
            removed_tiles=removed_tiles,
            board=current_board,
            played_time=played_time,
            previous_score=previous_score,
            img=warped,
        )
    except InvalidMoveExeption:
        current_move = Move(
            MoveType.UNKNOWN,
            player=player,
            coord=(0, 0),
            is_vertical=True,
            word='',
            new_tiles=new_tiles,
            removed_tiles=removed_tiles,
            board=current_board,
            played_time=played_time,
            previous_score=previous_score,
            img=warped,
        )

    return current_move


def _recalculate_score_on_tiles_change(game: Game, board: dict, changed: dict):
    """fix scores on changed tile recognition

    Args:
        game(Move): the game to fix
        board(dict): last analyzed board
        changed(dict): modified tiles of previous moves
    """

    logging.info(f'changed tiles: {changed}')
    to_inspect = min(config.scrabble_verify_moves, len(game.moves)) * -1
    prev_score = game.moves[to_inspect - 1].score if len(game.moves) > abs(to_inspect - 1) else (0, 0)
    must_recalculate = False
    for mov in game.moves[to_inspect:]:
        must_recalculate = must_recalculate or any(coord in mov.board for coord in changed)
        if must_recalculate:
            mov.board.update({coord: changed[coord] for coord in changed if coord in mov.board})
            _word = ''
            (col, row) = mov.coord
            for j, char in enumerate(mov.word):  # fix mov.word
                if mov.is_vertical:
                    _word += board[(col, row + j)][0] if char != '.' else '.'
                else:
                    _word += board[(col + j, row)][0] if char != '.' else '.'
            mov.word = _word
            mov.points, mov.score, mov.is_scrabble = mov.calculate_score(prev_score)
            prev_score = mov.score  # store previous score
            logging.info(f'move {mov.move} after recalculate {prev_score}')
        else:
            prev_score = mov.score  # store previous score
    return prev_score


def _store(game: Game, move_to_store: Optional[Move] = None, with_image: bool = True):  # pragma: no cover
    """store and upload move

    Args:
        game: current game
        move_index: index to store
        with_image: write img file
    """

    if config.is_testing:
        logging.info('skip store because flag is_testing is set')
        return

    if game.moves and move_to_store:
        if with_image and move_to_store.img is not None:
            if not cv2.imwrite(
                f'{config.web_dir}/image-{move_to_store.move}.jpg', move_to_store.img, [cv2.IMWRITE_JPEG_QUALITY, 100]
            ):
                logging.error(f'error writing image-{move_to_store.move}.jpg')
        try:
            with open(f'{config.web_dir}/data-{move_to_store.move}.json', 'w', encoding='UTF-8') as handle:
                handle.write(game.json_str(move_to_store.move))
            if game.moves[-1].move == move_to_store.move:
                logging.debug('write status.json')
                with open(f'{config.web_dir}/status.json', 'w', encoding='UTF-8') as handle:
                    handle.write(game.json_str(move_to_store.move))
        except OSError as error:
            logging.error(f'error writing game move {move_to_store.move}: {error}')
        _development_recording(game, None, info=True)

        if config.upload_server:
            pool.submit(upload.upload_move, move_to_store.move)
    else:
        try:
            logging.debug('upload status.json')
            with open(f'{config.web_dir}/status.json', 'w', encoding='UTF-8') as handle:
                handle.write(game.json_str())
            if config.upload_server:
                pool.submit(upload.upload_status)  # upload empty status
        except OSError as error:
            logging.error(f'error writing status.json: {error}')


def store_zip_from_game(game: Game):  # pragma: no cover
    """zip a game and upload to server"""
    import glob
    import os
    import uuid
    from zipfile import ZipFile

    if config.is_testing:
        logging.info('skip store because flag is_testing is set')
        return
    if game.gamestart is None:
        game.gamestart = datetime.now()
    game_id = game.gamestart.strftime('%y%j-%H%M%S')
    zip_filename = f'{game_id}-{str(uuid.uuid4())}'
    with ZipFile(f'{config.web_dir}/{zip_filename}.zip', 'w') as _zip:
        logging.info(f'create zip with {len(game.moves):d} files')
        for mov in game.moves:
            if os.path.exists(f'{config.web_dir}/image-{mov.move}.jpg'):
                _zip.write(f'{config.web_dir}/image-{mov.move}.jpg', arcname=f'image-{mov.move}.jpg')
            if os.path.exists(f'{config.web_dir}/data-{mov.move}.json'):
                _zip.write(f'{config.web_dir}/data-{mov.move}.json', arcname=f'data-{mov.move}.json')
        if os.path.exists(f'{config.log_dir}/messages.log'):
            _zip.write(f'{config.log_dir}/messages.log', arcname='messages.log')
        if config.development_recording:
            file_list = glob.glob(f'{config.work_dir}/recording/{game_id}-*')
            for filename in file_list:
                _zip.write(f'{filename}', arcname=f'recording/{os.path.basename(filename)}')
            if os.path.exists(f'{config.work_dir}/recording/gameRecording.log'):
                _zip.write(f'{config.work_dir}/recording/gameRecording.log', arcname='recording/gameRecording.log')
    if config.upload_server:
        upload.upload_game(f'{zip_filename}')


def _development_recording(
    game: Game, img: Optional[MatLike], suffix: str = '', info: bool = False, is_next_move: bool = False
):  # pragma: no cover
    if config.is_testing:
        logging.info('skip store because flag is_testing is set')
        return
    if config.development_recording:
        logging.debug(f'suffix "{suffix}" info {info}')
        recording_logger = logging.getLogger('gameRecordingLogger')
        if game.gamestart is None:
            game.gamestart = datetime.now()
        game_id = game.gamestart.strftime('%y%j-%H%M%S')
        if img is not None:
            move_number = len(game.moves) + 1 if is_next_move else len(game.moves)
            cv2.imwrite(
                f'{config.work_dir}/recording/{game_id}-{move_number}{suffix}.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 100]
            )
        if info and len(game.moves) > 0:
            try:
                warp_str = np.array2string(get_last_warp(), formatter={'float_kind': lambda x: f'{x:.1f}'}, separator=',')  # type: ignore[arg-type] # pylint: disable=C0301 # noqa: E501
            except AttributeError:
                warp_str = None
            recording_logger.info(f'{game_id} move: {game.moves[-1].move}')
            recording_logger.info(f'{game_id} warp: {warp_str}')
            recording_logger.info(f'{game_id} player: {game.moves[-1].player}')
            recording_logger.info(f'{game_id} coord: {game.moves[-1].coord} vertical: {game.moves[-1].is_vertical}')
            recording_logger.info(f'{game_id} word: {game.moves[-1].points}')
            recording_logger.info(f'{game_id} points: {game.moves[-1].points}')
            recording_logger.info(f'{game_id} score: {game.moves[-1].score}')
            recording_logger.info(f'{game_id} new tiles: {game.moves[-1].new_tiles}')
            recording_logger.info(f'{game_id} removed tiles: {game.moves[-1].removed_tiles}')
            recording_logger.info(f'{game_id} board: {game.moves[-1].board}')
