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
import copy
import logging
import time
from concurrent import futures
from concurrent.futures import Future
from typing import List, Optional, Tuple

import cv2
import imutils
import numpy as np

from classicboard import ClassicBoard
from config import config
from custom2012board import Custom2012Board
from custom2020board import Custom2020Board
from game_board.board import GRID_H, GRID_W, get_x_position, get_y_position
from game_board.tiles import tiles
from scrabble import Game, InvalidMoveExeption, Move, MoveType, NoMoveException
from threadpool import pool
from upload import upload
from util import runtime_measure, trace

Mat = np.ndarray[int, np.dtype[np.generic]]


def get_last_warp() -> Optional[Mat]:
    """Delegates the warp of the ``img`` according to the configured board style"""
    if config.video_warp and config.board_layout == 'classic':
        return ClassicBoard.last_warp
    if config.board_layout in ('custom', 'custom2012'):
        return Custom2012Board.last_warp
    if config.board_layout == 'custom2020':
        return Custom2020Board.last_warp
    return None


def clear_last_warp():
    """Delegates the warp of the ``img`` according to the configured board style"""
    if config.board_layout in ('custom', 'custom2012'):
        Custom2012Board.last_warp = None
    elif config.board_layout == 'custom2020':
        Custom2020Board.last_warp = None
    elif config.board_layout == 'classic':
        ClassicBoard.last_warp = None


@ runtime_measure
def warp_image(img: Mat) -> tuple[Mat, Mat]:
    """Delegates the warp of the ``img`` according to the configured board style"""
    logging.debug(f'({config.board_layout})')
    warped = img
    if config.video_warp and config.board_layout in ('custom', 'custom2012'):
        warped = Custom2012Board.warp(img)
    if config.video_warp and config.board_layout == 'custom2020':
        warped = Custom2020Board.warp(img)
    if config.video_warp and config.board_layout == 'classic':
        warped = ClassicBoard.warp(img)
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    return warped, warped_gray


@ runtime_measure
def filter_image(img: Mat) -> tuple[Optional[Mat], set]:
    """Delegates the image filter of the ``img`` according to the configured board style"""
    logging.debug(f'({config.board_layout})')
    if config.board_layout in ('custom', 'custom2012'):
        return Custom2012Board.filter_image(img)
    if config.board_layout == 'custom2020':
        return Custom2020Board.filter_image(img)
    if config.board_layout == 'classic':
        return ClassicBoard.filter_image(img)
    return None, set()


def filter_candidates(coord: tuple[int, int], candidates: set[tuple[int, int]], ignore_set: set[tuple[int, int]]) -> set:
    """ allow only valid field for analysis"""
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


def analyze(warped_gray: Mat, board: dict, coord_list: set[tuple[int, int]]) -> dict:
    """find tiles on board"""
    def match(img: Mat, suggest_tile: str, suggest_prop: int) -> tuple[str, int]:
        for _tile in tiles:
            res = cv2.matchTemplate(img, _tile.img, cv2.TM_CCOEFF_NORMED)  # type: ignore
            _, thresh, _, _ = cv2.minMaxLoc(res)
            if thresh > (suggest_prop / 100):
                suggest_tile = _tile.name
                suggest_prop = int(thresh * 100)
        return suggest_tile, suggest_prop

    def find_tile():
        (tile, prop) = board[coord] if coord in board else ('_', 76)
        if prop > 90:
            logging.debug(f"{chr(ord('A') + row)}{col + 1:2}: {tile} ({prop}) tile on board prop > 90 ")
            return board[coord]
        (tile, prop) = match(gray, tile, prop)
        if prop < 90:
            (tile, prop) = match(imutils.rotate(gray, -10), tile, prop)
        if prop < 90:
            (tile, prop) = match(imutils.rotate(gray, 10), tile, prop)
        board[coord] = (tile, prop) if tile is not None else ('_', 76)
        return board[coord]

    for coord in coord_list:
        (col, row) = coord
        _y = get_y_position(row)
        _x = get_x_position(col)
        gray = warped_gray[_y - 15:_y + GRID_H + 15, _x - 15:_x + GRID_W + 15]
        new_tile, new_prop = find_tile()
        logging.info(f"{chr(ord('A') + row)}{col + 1:2}: {new_tile} ({new_prop:2}) found")
    return board


def set_blankos(waitfor: Optional[Future], game: Game, coord: str, value: str, event=None):
    """set char for blanko

        Args:
        game(Move): the game to fix
        coord: coord of blank
        value: char for blank
        event: event to inform webservice
    """
    if waitfor is not None:                                                    # wait for previous moves
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'

    moves = game.moves
    logging.info(f'set blanko {coord} to {value}')

    for mov in moves:
        board = mov.board
        _, col, row = mov.calc_coord(coord)
        if (col, row) in board.keys() and (board[(col, row)][0] == '_' or board[(col, row)][0].islower()):
            board[(col, row)] = (value, board[(col, row)][1])
            if (col, row) in mov.new_tiles:
                mov.new_tiles[(col, row)] = value
                if mov.is_vertical:
                    mov.word = mov.word[:row - mov.coord[1]] + value + mov.word[row - mov.coord[1] + 1:]
                else:
                    mov.word = mov.word[:col - mov.coord[0]] + value + mov.word[col - mov.coord[0] + 1:]
    if event and not event.is_set():
        event.set()


def admin_insert_moves(waitfor: Optional[Future], game: Game, move_number: int, event=None):
    """insert two exchange moves before move number"""
    if waitfor is not None:                                                    # wait for previous moves
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
        img = game.moves[index].img.copy() if game.moves[index].img is not None else None  # type: ignore

        move1 = Move(MoveType.EXCHANGE, player=player1, coord=(0, 0), is_vertical=True, word='', new_tiles={},
                     removed_tiles={}, board=board, played_time=played_time,
                     previous_score=previous_score, img=img)
        move2 = Move(MoveType.EXCHANGE, player=player2, coord=(0, 0), is_vertical=True, word='', new_tiles={},
                     removed_tiles={}, board=board, played_time=played_time,
                     previous_score=previous_score, img=img)

        game.moves.insert(index, move2)
        game.moves.insert(index, move1)

        for i in range(index, len(game.moves)):
            game.moves[i].move = i + 1
            logging.debug(f'set/store move index {i} / move number {game.moves[i].move}')
            _store(game, i)
        if event and not event.is_set():
            event.set()
    else:
        logging.warning(f'wrong move number for insert after move: {move_number}')
        raise ValueError("invalid move number")


def admin_change_score(waitfor: Optional[Future], game: Game, move_number: int, score: Tuple[int, int], event=None):
    """fix scores (direct call from admin)

        Args:
        game(Move): the game to fix
        move_number: the move to fix(beginning with 1)
        score(Tuple[int, int]): new score
        event: event to inform webservice
    """
    if waitfor is not None:                                                    # wait for previous moves
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'

    if 0 < move_number <= len(game.moves):
        assert game.moves[move_number - 1].move == move_number
        index = move_number - 1
        delta = (game.moves[index].score[0] - score[0], game.moves[index].score[1] - score[1])
        if delta[0] != 0 or delta[1] != 0:
            game.moves[index].modification_cache['score'] = game.moves[index].score
        logging.debug(f'set score for move {move_number} {game.moves[index].score} => {score} / delta {delta}')
        for i in range(index, len(game.moves)):
            game.moves[i].score = (game.moves[i].score[0] - delta[0], game.moves[i].score[1] - delta[1])
            logging.info(f'move {i}: {game.moves[i].score}')
            _store(game, i, with_image=False)
        if event and not event.is_set():
            event.set()
    else:
        logging.warning(f'wrong move number for change score: {move_number}')
        raise ValueError("invalid move number")


def admin_change_move(waitfor: Optional[Future], game: Game, move_number: int, coord: Tuple[int, int], isvertical: bool,
                      word: str, event=None):
    # pylint: disable=too-many-arguments, too-many-locals,too-many-branches,too-many-statements
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
    if waitfor is not None:                                                    # wait for previous moves
        _, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'

    moves = game.moves
    if 0 < move_number <= len(moves):
        assert moves[move_number - 1].move == move_number
        assert 0 <= coord[0] < 15
        assert 0 <= coord[1] < 15

        index = move_number - 1

        logging.debug(f'try to fix move {move_number} at {coord} vertical={isvertical} with {word}')
        board = moves[index].board.copy()

        tiles_to_remove = moves[index].new_tiles.copy()                        # tiles to delete
        for elem in tiles_to_remove:
            del board[elem]                                                    # remove tiles on board from incorrect move
        logging.debug(f'tiles_to_remove {tiles_to_remove}')
        tiles_to_add: dict = {}                                                # tiles to add
        (col, row) = coord
        new_word = ''
        for i, char in enumerate(word):
            (xcol, xrow) = (col, row + i) if isvertical else (col + i, row)
            if (xcol, xrow) in board.keys():
                new_word += '.'
            else:
                new_word += char
                tiles_to_add[(xcol, xrow)] = (char, 99)
        word = new_word
        logging.debug(f'tiles_to_add {tiles_to_add} / word {new_word}')
        if tiles_to_remove or tiles_to_add:
            game.moves[index].modification_cache['coord'] = coord
            game.moves[index].modification_cache['isvertical'] = isvertical
            game.moves[index].modification_cache['word'] = word

        previous_board = game.moves[index - 1].board if move_number > 1 else {}
        previous_score = game.moves[index - 1].score if move_number > 1 else (0, 0)

        for i in range(index, len(moves)):
            new_move = copy.deepcopy(moves[i])                                 # board, img, score

            for elem in tiles_to_remove:                                       # repair board
                if elem in new_move.board.keys() and new_move.board[elem] == tiles_to_remove[elem]:
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
                new_move = _move_processing(game, new_move.player, new_move.played_time, new_move.img,
                                            new_move.board, previous_board, previous_score)
                new_move.modification_cache = save_cache
            new_move.move = i + 1
            previous_board = new_move.board
            previous_score = new_move.score
            moves[i] = new_move
            logging.info(f'recalculate move #{moves[i].move} ({moves[i].type}) '
                         f'new points {moves[i].points} new score {moves[i].score}')
            logging.info(f'\n{game.board_str(i)}')
            _store(game, i, with_image=False)
    else:
        logging.warning(f'wrong move number for change move: {move_number}')
        raise ValueError("invalid move number")
    if event and not event.is_set():
        event.set()


@ trace
def move(waitfor: Optional[Future], game: Game, img: Mat, player: int, played_time: Tuple[int, int], event=None):
    # pylint: disable=too-many-arguments
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

    previous_board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}   # get previous board information
    previous_score = game.moves[-1].score if len(game.moves) > 0 else (0, 0)

    current_move = _move_processing(game, player, played_time, warped, board, previous_board, previous_score)

    game.add_move(current_move)                                                # 9. add move
    if event and not event.is_set():
        event.set()

    logging.info(f'\n{game.board_str()}')
    if logging.getLogger('root').isEnabledFor(logging.DEBUG):
        msg = '\n'
        for i in range(0, len(game.moves)):  # pylint: disable=consider-using-enumerate
            msg += f'{game.moves[i].gcg_str(game.nicknames)}\n'
        logging.debug(f'{msg}\napi: {game.json_str()}\nscores: {game.moves[-1].score}')
    _development_recording(game, img, suffix='~original')
    _development_recording(game, warped, suffix='~warped')
    _store(game, -1)


@ trace
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
        _store(game, -1)
    except Exception as oops:  # pylint: disable=broad-exception-caught
        logging.error(f'exception on valid_challenge {oops}')
        logging.info('no new move')


@ trace
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
        game.add_invalid_challenge(player, played_time)                            # 9. add move
        if event and not event.is_set():
            event.set()

        logging.info(f'new scores {game.moves[-1].score}: {game.json_str()}\n{game.board_str()}')
        _store(game, -1)
    except Exception as oops:  # pylint: disable=broad-exception-caught
        logging.error(f'exception on in_valid_challenge {oops}')
        logging.info('no new move')


@ trace
def store_status(game: Game):
    """store current status.json - does not update data - *.json !"""
    _store(game, 0)


@ trace
def start_of_game(game: Game):
    """ start of game """
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
        if len(file_list) > 0:
            util.rotate_logs()
    except OSError:
        logging.error('OS Error on delete web data/image files')
    _store(game, 0)


@ trace
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
        logging.info(f'last rack scores {game.moves[-1].score}\n{game.board_str()}\n{game.json_str()}')
        if config.development_recording:
            logging.info(game.dev_str())

        _store(game, -2)
        _store(game, -1)


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
    for i in range(-1, len(game.moves) * -1, -1):
        mov = game.moves[i]
        bag = calculate_bag(mov)
        if len(bag) >= 14:  # now find changed tiles
            mov = game.moves[i]
            bag = calculate_bag(mov)
            bag_len = len(bag) - 14
            break
    rack = [7, 7]
    for j in range(i + 1, 0):  # type: ignore
        mov = game.moves[j]
        mov_len = len(mov.new_tiles)
        from_bag = min(mov_len, bag_len)
        rack[mov.player] -= (mov_len - from_bag)
        bag_len -= from_bag
        logging.info(f'player={mov.player} rack-size={rack[mov.player]} from-bag={from_bag}')
    if len(game.moves) > 0:
        bag = calculate_bag(game.moves[-1])
        points = 0
        for elem in bag:
            points += scores(elem)
        if rack[0] == 0 and rack[1] > 0:
            return (points, -points), "".join(bag)
        if rack[1] == 0 and rack[0] > 0:
            return (-points, points), "".join(bag)
    return (0, 0), '?'


def _changes(board: dict, previous_board: dict) -> Tuple[dict, dict, dict, dict]:
    for i in previous_board.keys():
        if i in board.keys() and previous_board[i][1] > board[i][1]:
            logging.debug(f'use value from old board {i}')
            board[i] = previous_board[i]
    new_tiles = {i: board[i] for i in set(board.keys()).difference(previous_board)}
    removed_tiles = {i: previous_board[i] for i in set(previous_board.keys()).difference(board)}
    changed_tiles = {i: board[i] for i in previous_board if
                     i not in removed_tiles and previous_board[i][0] != board[i][0]}
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
        vertical = ((col, row - 1) in board) or ((col, row + 1) in board) if not horizontal else False
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


@ runtime_measure
def _image_processing(waitfor: Optional[Future], game: Game, img: Mat) -> Tuple[Mat, dict]:
    # pylint: disable=too-many-locals
    if waitfor is not None:                                                    # wait for previous moves
        done, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'
    warped, warped_gray = warp_image(img)                                      # 1. warp image if necessary
    filtered_image, tiles_candidates = filter_image(warped)                    # 3. find potential tiles on board
    _development_recording(game, filtered_image, suffix='~filter', is_next_move=True)

    if len(game.moves) > 1:                                                    # 3a. check for wrong blank tiles
        to_del = [i for i in game.moves[-1].new_tiles.keys() if (game.moves[-1].board[i][0] == '_')
                  and i not in tiles_candidates]  # noqa: W503
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
                {i: i for i in game.moves[-1 * config.scrabble_verify_moves + 1].board.keys()
                 if i in game.moves[-1].board.keys()})
        else:
            ignore_coords = set(
                {i: i for i in game.moves[-1 * config.scrabble_verify_moves].board.keys() if i in game.moves[-1].board.keys()})
    tiles_candidates = tiles_candidates | ignore_coords                        # tiles_candidates must contain ignored_coords
    filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
    logging.debug(f'filtered_candidates {filtered_candidates}')

    board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}         # copy board for analyze
    chunks = _chunkify(list(filtered_candidates), 3)                           # 5. picture analysis
    future1 = pool.submit(analyze, warped_gray, board, set(chunks[0]))           # 1. thread
    future2 = pool.submit(analyze, warped_gray, board, set(chunks[1]))           # 2. thread
    analyze(warped_gray, board, set(chunks[2]))                                  # 3. (this) thread
    done, _ = futures.wait({future1, future2})                                 # 6. blocking wait
    assert len(done) == 2, 'error on wait to futures'
    return warped, board


def _move_processing(game: Game, player: int, played_time: Tuple[int, int], warped, board: dict, previous_board: dict,
                     previous_score: Tuple[int, int]) -> Move:
    # pylint: disable=too-many-arguments
    current_board, new_tiles, removed_tiles, changed_tiles = _changes(board, previous_board)  # find changes on board
    if len(changed_tiles) > 0:                                                 # 7. fix old moves
        previous_score = _recalculate_score_on_tiles_change(game, board, changed_tiles)
    try:                                                                       # 8. find word and create move
        is_vertical, coord, word = _find_word(current_board, sorted(new_tiles))
        current_move = Move(MoveType.REGULAR, player=player, coord=coord, is_vertical=is_vertical, word=word,
                            new_tiles=new_tiles, removed_tiles=removed_tiles, board=current_board, played_time=played_time,
                            previous_score=previous_score, img=warped)
    except NoMoveException:
        current_move = Move(MoveType.EXCHANGE, player=player, coord=(0, 0), is_vertical=True, word='', new_tiles=new_tiles,
                            removed_tiles=removed_tiles, board=current_board, played_time=played_time,
                            previous_score=previous_score, img=warped)
    except InvalidMoveExeption:
        current_move = Move(MoveType.UNKNOWN, player=player, coord=(0, 0), is_vertical=True, word='', new_tiles=new_tiles,
                            removed_tiles=removed_tiles, board=current_board, played_time=played_time,
                            previous_score=previous_score, img=warped)

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
    for mov in reversed(game.moves[to_inspect:]):
        must_recalculate = must_recalculate or any(coord in mov.board.keys() for coord in changed.keys())
        if must_recalculate:
            mov.board.update({coord: changed[coord] for coord in changed.keys() if coord in mov.board.keys()})
            _word = ''
            (col, row) = mov.coord
            for j, char in enumerate(mov.word):                                # fix mov.word
                if mov.is_vertical:
                    _word += board[(col, row + j)][0] if char != '.' else '.'
                else:
                    _word += board[(col + j, row)][0] if char != '.' else '.'
            mov.word = _word
            mov.points, prev_score, mov.is_scrabble = mov.calculate_score(prev_score)
            mov.score = prev_score                                             # store previous score
            logging.info(f'move {mov.move} after recalculate {prev_score}')
        else:
            prev_score = mov.score                                             # store previous score
    return prev_score


def _store(game: Game, move_index: int, with_image: bool = True):  # pragma: no cover
    """ store and upload move

    Args:
        game: current game
        move_index: index to store
        with_image: write img file
    """

    if config.is_testing:
        logging.info('skip store because flag is_testing is set')
        return
    moves = game.moves
    if len(moves) < 1:
        try:
            logging.debug('empty game - upload empty status.json')
            with open(f'{config.web_dir}/status.json', "w", encoding='UTF-8') as handle:
                handle.write(game.json_str())
            if config.upload_server:
                pool.submit(upload.upload_status)                    # upload empty status
        except IOError as error:
            logging.error(f'error writing game move {move_index}: {error}')
    elif -len(moves) <= move_index < len(moves):
        if with_image and moves[move_index].img is not None:
            if not cv2.imwrite(f'{config.web_dir}/image-{moves[move_index].move}.jpg',
                               moves[move_index].img, [cv2.IMWRITE_JPEG_QUALITY, 99]):  # type: ignore
                logging.error(f'error writing image-{moves[move_index].move}.jpg')
        try:
            with open(f'{config.web_dir}/data-{game.moves[move_index].move}.json', "w", encoding='UTF-8') as handle:
                handle.write(game.json_str(game.moves[move_index].move))
            if game.moves[-1].move == game.moves[move_index].move:
                logging.debug('write status.json')
                with open(f'{config.web_dir}/status.json', "w", encoding='UTF-8') as handle:
                    handle.write(game.json_str(moves[move_index].move))
        except IOError as error:
            logging.error(f'error writing game move {moves[move_index].move}: {error}')
        _development_recording(game, None, info=True)

        if config.upload_server:
            pool.submit(upload.upload_move, moves[move_index].move)


def store_zip_from_game(game: Game):  # pragma: no cover
    """zip a game and upload to server"""
    import glob
    import os
    import uuid
    from zipfile import ZipFile

    if config.is_testing:
        logging.info('skip store because flag is_testing is set')
        return
    game_id = game.gamestart.strftime("%y%j-%H%M%S")  # type: ignore
    zip_filename = f'{game_id}-{str(uuid.uuid4())}'
    with ZipFile(f'{config.web_dir}/{zip_filename}.zip', 'w') as _zip:
        logging.info(f"create zip with {len(game.moves):d} files")
        for i in range(1, len(game.moves) + 1):
            if os.path.exists(f'{config.web_dir}/image-{i}.jpg'):
                _zip.write(f'{config.web_dir}/image-{i}.jpg', arcname=f'image-{i}.jpg')
            if os.path.exists(f'{config.web_dir}/data-{i}.json'):
                _zip.write(f'{config.web_dir}/data-{i}.json', arcname=f'data-{i}.json')
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


def _development_recording(game: Game, img: Optional[Mat], suffix: str = '', info: bool = False,
                           is_next_move: bool = False):  # pragma: no cover

    if config.is_testing:
        logging.info('skip store because flag is_testing is set')
        return
    if config.development_recording:
        logging.debug(f'suffix "{suffix}" info {info}')
        recording_logger = logging.getLogger("gameRecordingLogger")
        game_id = game.gamestart.strftime("%y%j-%H%M%S")  # type: ignore
        if img is not None:
            move_number = len(game.moves) + 1 if is_next_move else len(game.moves)
            cv2.imwrite(f'{config.work_dir}/recording/{game_id}-{move_number}{suffix}.jpg',
                        img, [cv2.IMWRITE_JPEG_QUALITY, 99])
        if info and len(game.moves) > 0:
            try:
                warp_str = np.array2string(get_last_warp(), formatter={  # type: ignore
                    'float_kind': lambda x: f'{x:.1f}'}, separator=',')
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
