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
from concurrent import futures
from datetime import datetime
from typing import List, Optional, Tuple

import cv2
import imutils
from cv2.typing import MatLike

from config import config
from custom2012board import Custom2012Board
from custom2020board import Custom2020Board
from custom2020light import Custom2020LightBoard
from game_board.board import GRID_H, GRID_W, get_x_position, get_y_position
from game_board.tiles import tiles
from scrabble import Game, InvalidMoveExeption, Move, MoveType, NoMoveException
from threadpool import pool
from upload import upload
import upload_impl
from util import TWarp, runtime_measure, trace

ANALYZE_THREADS = 4
BOARD_CLASSES = {'custom2012': Custom2012Board, 'custom2020': Custom2020Board, 'custom2020light': Custom2020LightBoard}
BLANK_PROP = 76
MATCH_ROTATIONS = [0, -5, 5, -10, 10, -15, 15]
THRESHOLD_PROP_BOARD = 97
THRESHOLD_PROP_TILE = 86
THRESHOLD_UMLAUT_BONUS = 2
UMLAUTS = ('Ä', 'Ü', 'Ö')
ORD_A = ord('A')


def get_last_warp() -> Optional[TWarp]:  # pylint: disable=too-many-return-statements
    """Delegates the warp of the ``img`` according to the configured board style"""
    return BOARD_CLASSES.get(config.board.layout, Custom2012Board).last_warp


def clear_last_warp():
    """Delegates the last_warp according to the configured board style"""
    BOARD_CLASSES.get(config.board.layout, Custom2012Board).last_warp = None


@runtime_measure
def warp_image(img: MatLike) -> tuple[MatLike, MatLike]:
    """Delegates the warp of the ``img`` according to the configured board style"""
    warped = BOARD_CLASSES.get(config.board.layout, Custom2012Board).warp(img) if config.video.warp else img
    return warped, cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)


@runtime_measure
def filter_image(img: MatLike) -> tuple[Optional[MatLike], set]:  # pylint: disable=too-many-return-statements
    """Delegates the image filter of the ``img`` according to the configured board style"""
    return BOARD_CLASSES.get(config.board.layout, Custom2012Board).filter_image(img)


def event_set(event):
    """set event and skips set if event is None. Informs the webservice about the end of the task"""
    if event is not None:
        event.set()


DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def filter_candidates(
    coord: tuple[int, int], candidates: set[tuple[int, int]], ignore_set: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    """allow only valid field for analysis"""
    candidates = candidates.copy()
    result = set()
    stack = [coord]
    while stack:
        col, row = stack.pop()
        if (col, row) not in candidates:
            continue
        candidates.remove((col, row))
        if (col, row) not in ignore_set:
            result.add((col, row))
        stack.extend([(col + dx, row + dy) for dx, dy in DIRECTIONS])
    return result


def analyze(warped_gray: MatLike, board: dict, coord_list: set[tuple[int, int]]) -> dict:
    """find tiles on board"""
    match_calls = 0

    def match_tile(img: MatLike, suggest_tile: str, suggest_prop: int) -> tuple[str, int]:
        nonlocal match_calls

        for _tile in tiles:
            res = cv2.matchTemplate(img, _tile.img, cv2.TM_CCOEFF_NORMED)
            match_calls += 1
            _, thresh, _, _ = cv2.minMaxLoc(res)
            thresh = int(thresh * 100)
            if _tile.name in UMLAUTS and thresh > suggest_prop - THRESHOLD_UMLAUT_BONUS:
                thresh = min(99, thresh + THRESHOLD_UMLAUT_BONUS)  # 2% Bonus for umlauts
                logging.debug(f'{chr(ORD_A + row)}{col + 1:2} => ({_tile.name},{thresh}) increased prop')
            if thresh > suggest_prop:
                suggest_tile, suggest_prop = _tile.name, thresh
        return suggest_tile, suggest_prop

    def find_tile(gray, tile):
        (tile, prop) = tile
        if prop > THRESHOLD_PROP_BOARD:
            logging.debug(f'{chr(ORD_A + row)}{col + 1:2}: {tile} ({prop}) tile on board prop > {THRESHOLD_PROP_BOARD} ')
            return (tile, prop)

        for angle in MATCH_ROTATIONS:
            tile, prop = match_tile(imutils.rotate(gray, angle), tile, prop)
            if prop >= config.board.min_tiles_rate:
                break

        board[coord] = (tile, prop) if tile is not None and prop > THRESHOLD_PROP_TILE else ('_', BLANK_PROP)
        return (tile, prop)

    for coord in coord_list:
        (col, row) = coord
        x, y = get_x_position(col), get_y_position(row)
        segment = warped_gray[y - 15 : y + GRID_H + 15, x - 15 : x + GRID_W + 15]
        board[coord] = find_tile(segment, board.get(coord, ('_', BLANK_PROP)))
        logging.info(f'{chr(ORD_A + row)}{col + 1:2}: {board[coord]}) found')
    logging.debug(f'templateMatch calls: {match_calls}')
    return board


def analyze_threads(warped_gray: MatLike, board: dict, candidates: set[tuple[int, int]]):
    """start threads for analyze"""
    from concurrent.futures import ThreadPoolExecutor

    def chunkify(lst, chunks):
        return [lst[i::chunks] for i in range(chunks)]

    chunks = chunkify(list(candidates), ANALYZE_THREADS)  # chunks for picture analysis
    analyze_futures = []
    with ThreadPoolExecutor(max_workers=ANALYZE_THREADS, thread_name_prefix='analyze') as executor:
        for i in range(ANALYZE_THREADS):
            board_chunk = {key: board[key] for key in chunks[i] if key in board}
            analyze_futures.append(executor.submit(analyze, warped_gray, board_chunk, set(chunks[i])))
        done, not_done = futures.wait(analyze_futures)  # blocking wait
        for f in done:
            board.update(f.result())
        for e in not_done:
            logging.error(f'Error during analyze future: {e.exception}')
    return board


def remove_blanko(game: Game, gcg_coord: str, event=None):
    """remove blank

    Args:
    game(Move): the game to fix
    coord: coord of blank
    event: event to inform webservice
    """
    logging.info(f'remove blanko {gcg_coord}')
    if game.moves:
        _, col, row = game.moves[-1].calc_coord(gcg_coord)
        coord = (col, row)
        index = -1
        for elem in game.moves:  # noqa: B007 # find first occurrence of blanko
            board = elem.board
            if coord in board and (board[coord][0] == '_' or board[coord][0].islower()):
                index = game.moves.index(elem)
                del board[coord]
                break
        if index > -1:
            tiles_to_add: dict = {}
            tiles_to_remove: dict = {}
            tiles_to_remove[coord] = ('_', 76)
            previous_board = game.moves[index - 1].board if index > 0 else {}
            previous_score = game.moves[index - 1].score if index > 0 else (0, 0)
            admin_recalc_moves(game, index, tiles_to_remove, tiles_to_add, previous_board, previous_score)
            for mov in game.moves[index:]:
                write_files(game, mov, only_json=True)
    event_set(event)


def set_blankos(game: Game, gcg_coord: str, value: str, event=None):
    """set char for blanko

    Args:
    game(Move): the game to fix
    coord: coord of blank
    value: char for blank
    event: event to inform webservice
    """
    logging.info(f'set blanko {gcg_coord} to {value}')
    if game.moves:
        _, col, row = game.moves[-1].calc_coord(gcg_coord)
        coord = (col, row)
        for mov in game.moves:
            board = mov.board
            if coord in board and (board[coord][0] == '_' or board[coord][0].islower()):
                board[coord] = (value, board[coord][1])
                if coord in mov.new_tiles:
                    mov.new_tiles[coord] = (value.lower()[:1], mov.new_tiles[coord][1])
                    index = row - mov.coord[1] if mov.is_vertical else col - mov.coord[0]
                    mov.word = f'{mov.word[:index]}{value}{mov.word[index + 1 :]}'
    event_set(event)


def admin_insert_moves(game: Game, move_number: int, event=None):  # pylint: disable=too-many-locals
    """insert two exchange moves before move number"""

    if move_number <= 0 or move_number > len(game.moves):
        raise ValueError('invalid move number {move_number}')

    logging.info(f'insert before move {move_number}')
    move_index = move_number - 1
    player1, player2 = (game.moves[move_index].player, (game.moves[move_index].player + 1) % 2)
    board = game.moves[move_index - 1].board.copy() if move_index > 0 else {}
    played_time = game.moves[move_index - 1].played_time if move_index > 0 else (0, 0)
    previous_score = game.moves[move_index - 1].score if move_index > 0 else (0, 0)
    img = game.moves[move_index].img.copy() if game.moves[move_index].img is not None else None  # type: ignore[attr-defined]

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
    move2 = copy.deepcopy(move1)
    move2.player = player2

    game.moves.insert(move_index, move2)
    game.moves.insert(move_index, move1)

    for i, mov in enumerate(game.moves[move_index:]):
        mov.move = i + move_index + 1
        logging.debug(f'set/store move index {move_index + i} / move number {mov.move}')
        write_files(game, mov)
    event_set(event)


def admin_change_score(game: Game, move_number: int, new_score: Tuple[int, int], event=None):
    """fix scores (direct call from admin)"""

    if move_number <= 0 or move_number > len(game.moves):
        raise ValueError('invalid move number {move_number}')
    move_index = move_number - 1
    mov = game.moves[move_index]
    delta = (mov.score[0] - new_score[0], mov.score[1] - new_score[1])
    if delta != (0, 0):  # score change
        mov.modification_cache['score'] = mov.score
        logging.debug(f'set score for move {move_number} {mov.score} => {new_score} / delta {delta}')
        for mov in game.moves[move_index:]:
            mov.score = (mov.score[0] - delta[0], mov.score[1] - delta[1])
            logging.info(f'>> move {mov.move}: new score {mov.score}')
            write_files(game, mov, only_json=True)
    event_set(event)


def admin_change_move(game: Game, move_number: int, coord: Tuple[int, int], isvertical: bool, word: str, event=None):
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
    for m in game.moves[index:]:
        write_files(game, m, only_json=True)
    event_set(event)


def admin_recalc_moves(
    game: Game, index: int, tiles_to_remove: dict, tiles_to_add: dict, previous_board: dict, previous_score: Tuple[int, int]
):  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """recalculate move scores and points after admin changes"""

    def update_board(m: Move, tiles_to_remove: dict, tiles_to_add: dict):
        for elem in tiles_to_remove:
            m.board.pop(elem, None)
        m.board |= tiles_to_add

    def update_score_for_bonus(m: Move, prev_score: Tuple[int, int]):
        penalty = config.scrabble.malus_doubt
        m.score = (prev_score[0] - penalty, prev_score[1]) if m.player == 0 else (prev_score[0], prev_score[1] - penalty)

    def update_withdrawn_move(m: Move, prev_move: Move):
        m.points = -prev_move.points
        m.word = prev_move.word
        m.removed_tiles = prev_move.new_tiles
        m.new_tiles = {}

    moves = game.moves
    logging.debug(f'{index=} {tiles_to_remove=} {tiles_to_add=} {previous_score=}')
    for i in range(index, len(moves)):
        new_move = copy.deepcopy(moves[i])  # board, img, score
        update_board(new_move, tiles_to_remove, tiles_to_add)

        match new_move.type:
            case MoveType.CHALLENGE_BONUS:
                update_score_for_bonus(new_move, previous_score)
            case MoveType.WITHDRAW:
                update_withdrawn_move(new_move, moves[i - 1])
            case _:
                save_cache = new_move.modification_cache
                new_move = _move_processing(
                    game, new_move.player, new_move.played_time, new_move.img, new_move.board, previous_board, previous_score
                )
                new_move.modification_cache = save_cache
        new_move.move = i + 1
        previous_board = new_move.board
        previous_score = new_move.score
        moves[i] = new_move
        logging.info(f'#{moves[i].move} ({moves[i].type}) new points {moves[i].points} new score {moves[i].score}')
        logging.debug(f'\n{game.board_str(i)}')


def admin_del_challenge(game: Game, move_number: int, event=None):
    """delete challenge move number"""
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
    for m in game.moves[index:]:
        write_files(game, m)
    event_set(event)


def admin_toggle_challenge_type(game: Game, move_number: int, event=None):
    """toggle challenge type on move number"""

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
        to_change.points = config.scrabble.malus_doubt * -1
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
    for m in game.moves[index:]:
        write_files(game, m, only_json=True)
    event_set(event)


def admin_ins_challenge(game: Game, move_number: int, move_type: MoveType, event=None):
    """insert invalid challenge or withdraw for move number"""

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
        to_insert.points = config.scrabble.malus_doubt * -1
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

    previous_board = game.moves[index].board if index >= 0 else {}
    previous_score = game.moves[index].score if index >= 0 else (0, 0)
    for i in range(index + 1, len(game.moves)):
        game.moves[i].move += 1
    admin_recalc_moves(game, index + 1, to_insert.removed_tiles, {}, previous_board, previous_score)
    for m in game.moves[index:]:
        write_files(game, m)
    event_set(event)


# @trace
def move(game: Game, img: MatLike, player: int, played_time: Tuple[int, int], event=None):
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    """Process a move"""
    warped, board = _image_processing(game, img)

    previous_board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}  # get previous board information
    previous_score = game.moves[-1].score if len(game.moves) > 0 else (0, 0)

    current_move = _move_processing(game, player, played_time, warped, board, previous_board, previous_score)

    game.add_move(current_move)  # 9. add move
    event_set(event)

    logging.info(f'\n{game.board_str()}')
    if logging.getLogger('root').isEnabledFor(logging.DEBUG):
        msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str(game.nicknames)}\n' for mov in game.moves)
        logging.debug(
            f'{msg}\nscores: {game.moves[-1].score}\napi: {game.json_str()[: game.json_str().find("moves") + 7]}...\n'
        )
    write_files(game, game.moves[-1], img)


@trace
def check_resume(
    game: Game, image: MatLike, player: int, played_time: Tuple[int, int], current_time: Tuple[int, int], event=None
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """check resume"""

    last_move = game.moves[-1] if game.moves else None
    if last_move is not None and last_move.type == MoveType.REGULAR:  # only check regular moves
        if not last_move.new_tiles:  # no new tiles in last move
            return
        warped, _ = warp_image(image)
        _, tiles_candidates = filter_image(warped)
        intersection = set(last_move.new_tiles.keys()) & set(tiles_candidates)
        if intersection == set():  #  empty set => tiles are removed
            valid_challenge(game, player, played_time, event)
            logging.info(f'automatic valid challenge (move time {current_time[player]} sec)')
        # else: # uncomment if you want a invalid challenges as default on resume
        #     invalid_challenge(game, player, played_time, event)
        #     logging.info(f'automatic invalid challenge (move time {current_time[player]} sec)')


@trace
def valid_challenge(game: Game, player: int, played_time: Tuple[int, int], event=None):
    """Process a valid challenge"""

    try:
        game.add_valid_challenge(player, played_time)
        event_set(event)

        logging.info(f'new scores {game.moves[-1].score}: {game.json_str()}\n{game.board_str()}')
        write_files(game, game.moves[-1])
    except Exception as oops:  # pylint: disable=broad-exception-caught
        logging.error(f'exception on valid_challenge {oops}')
        logging.info('no new move')


@trace
def invalid_challenge(game: Game, player: int, played_time: Tuple[int, int], event=None):
    """Process an invalid challenge"""

    try:
        game.add_invalid_challenge(player, played_time)  # 9. add move
        event_set(event)

        logging.info(f'new scores {game.moves[-1].score}: {game.json_str()}\n{game.board_str()}')
        write_files(game, game.moves[-1])
    except Exception as oops:  # pylint: disable=broad-exception-caught
        logging.error(f'exception on in_valid_challenge {oops}')
        logging.info('no new move')


@trace
def start_of_game(game: Game):
    """start of game"""
    import glob
    import os

    import util

    upload_impl.last_future = pool.submit(
        upload.delete_files, upload_impl.last_future
    )  # first delete images and data files on ftp server
    try:
        file_list = glob.glob(f'{config.path.web_dir}/image-*.jpg')
        file_list += glob.glob(f'{config.path.web_dir}/data-*.json')
        for file_path in file_list:
            os.remove(file_path)
        if file_list:
            util.rotate_logs()
    except OSError:
        logging.error('OS Error on delete web data/image files')
    write_files(game)  # only status file


@trace
def end_of_game(game: Game, event=None):
    # pragma: no cover #pylint: disable=too-many-locals # no ftp upload on tests
    """Process end of game"""
    from contextlib import suppress

    def calculate_rack(game: Game) -> Tuple[Tuple[int, int], str]:
        from game_board.tiles import bag_as_list, scores

        with suppress(Exception):  # possible exception, if bag is invalid because of wrong recognition
            bag = bag_as_list.copy()
            rack = [7, 7]
            bag_len = len(bag) - 14  # both rack are filled wit 7 tiles
            for mov in game.moves:
                if mov.type == MoveType.WITHDRAW:
                    mov_len = len(mov.removed_tiles)
                    tiles_from_bag = min((rack[mov.player] + mov_len - 7) * -1, 0)  # tiles to put back
                    rack[mov.player] = min(rack[mov.player] + mov_len, 7)  # tiles on rack
                    for v, _ in mov.removed_tiles.values():
                        bag.append(v)
                else:
                    mov_len = len(mov.new_tiles)
                    tiles_from_bag = min(mov_len, bag_len)  # tiles available in bag
                    rack[mov.player] = rack[mov.player] - (mov_len - tiles_from_bag)  # tiles on rack
                    for v, _ in mov.new_tiles.values():
                        bag.remove('_' if v.isalpha() and v.islower() else v)
                bag_len -= tiles_from_bag
                if rack != [7, 7]:
                    logging.debug(
                        f'move {mov.move} ({mov.type}) player={mov.player} rack={rack} '
                        f'tiles_from_bag={tiles_from_bag} bag_len={bag_len}'
                    )
            points = sum(scores(elem) for elem in bag)
            logging.debug(f'last rack {rack} {bag} {points=}')
            if (rack[0] == 0) != (rack[1] == 0):  # xor
                return (points, -points) if rack[0] == 0 else (-points, points), ''.join(sorted(bag))
        return (0, 0), '?'

    if game.moves:
        # calculate overtime malus
        t = (config.scrabble.max_time - game.moves[-1].played_time[0], config.scrabble.max_time - game.moves[-1].played_time[1])
        logging.debug(f'overtime {t=}')
        for player in range(2):
            if t[player] < 0:  # in overtime
                malus = (t[player] // 60) * config.scrabble.timeout_malus  # config.timeout_malus per minute
                game.add_timout_malus(player, malus)  # add as move

        with suppress(Exception):
            points, rackstr = calculate_rack(game)
            game.add_last_rack(points, rackstr)
            write_files(game, game.moves[-2])
            write_files(game, game.moves[-1])

        event_set(event)
        msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str(game.nicknames)}\n' for mov in game.moves)
        logging.debug(
            f'last rack scores:\n{game.board_str()}{msg}\nscores: {game.moves[-1].score}\n'
            f'api: {game.json_str()[: game.json_str().find("moves") + 7]}...\n'
        )
        logging.info(game.dev_str())


def _changes(board: dict, previous_board: dict) -> Tuple[dict, dict, dict, dict]:
    for coord, (prev_value, prev_score) in previous_board.items():
        if coord in board and prev_score > board[coord][1]:
            logging.debug(f'use value from old board {coord}')
            board[coord] = (prev_value, prev_score)
    new_tiles = {i: board[i] for i in set(board.keys()).difference(previous_board)}
    removed_tiles = {i: previous_board[i] for i in set(previous_board.keys()).difference(board)}
    changed_tiles = {i: board[i] for i in previous_board if i not in removed_tiles and previous_board[i][0] != board[i][0]}
    return board, new_tiles, removed_tiles, changed_tiles


def _find_word(board: dict, changed: List) -> Tuple[bool, Tuple[int, int], str]:
    if len(changed) < 1:
        logging.info('move: no new tiles detected')
        raise NoMoveException('move: no new tiles')
    horizontal = len({col for col, _ in changed}) > 1
    vertical = len({row for _, row in changed}) > 1
    if vertical and horizontal:
        logging.warning(f'illegal move: {changed}')
        raise InvalidMoveExeption('move: illegal move horizontal and vertical changes detected')

    col, row = start = changed[0]
    if len(changed) == 1:  # only 1 tile
        horizontal = ((col - 1, row) in board) or ((col + 1, row) in board)
        vertical = not horizontal

    direction = (0, 1) if vertical else (1, 0)  # (dx, dy)
    while (col - direction[0], row - direction[1]) in board:  # find start position
        (col, row) = (col - direction[0], row - direction[1])
    start = (col, row)

    word = ''
    while (col, row) in board:  # build word
        word += board[(col, row)][0] if (col, row) in changed else '.'
        (col, row) = (col + direction[0], row + direction[1])
    return vertical, start, word


@runtime_measure
def _image_processing(game: Game, img: MatLike) -> Tuple[MatLike, dict]:
    # pylint: disable=too-many-locals

    warped, warped_gray = warp_image(img)  # 1. warp image if necessary
    _, tiles_candidates = filter_image(warped)  # 3. find potential tiles on board

    if len(game.moves) > 1:  # 3a. check for wrong blank tiles
        to_del = [i for i in game.moves[-1].new_tiles if (game.moves[-1].board[i][0] == '_') and i not in tiles_candidates]
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
    if len(game.moves) > config.scrabble.verify_moves:
        # if opponents move has a valid challenge
        if game.moves[-1 * config.scrabble.verify_moves + 1].type in (MoveType.PASS_TURN, MoveType.EXCHANGE, MoveType.WITHDRAW):
            ignore_coords = set(
                {i: i for i in game.moves[-1 * config.scrabble.verify_moves + 1].board if i in game.moves[-1].board}
            )
        else:
            ignore_coords = set(
                {i: i for i in game.moves[-1 * config.scrabble.verify_moves].board if i in game.moves[-1].board}
            )
    tiles_candidates |= ignore_coords  # tiles_candidates must contain ignored_coords
    tiles_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
    logging.debug(f'filtered_candidates {tiles_candidates}')

    board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}  # copy board for analyze
    return warped, analyze_threads(warped_gray, board, tiles_candidates)


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
    to_inspect = min(config.scrabble.verify_moves, len(game.moves)) * -1
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


def write_files(
    game: Game, move_to_store: Optional[Move] = None, dev_img: Optional[MatLike] = None, only_json: bool = False
):  # pragma: no cover
    """Write game data and images to disk."""

    def write_json_file(name: str, content: str):
        try:
            with open(name, 'w', encoding='UTF-8') as f:
                f.write(content)
        except OSError as e:
            logging.error(f'Error writing {name}: {e}')

    def save_image(path: str, img: MatLike):
        if not cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 100]):
            logging.error(f'Error writing image: {path}')

    def write_dev_log_entry():
        logger = logging.getLogger('gameRecordingLogger')
        if game.gamestart is None:
            game.gamestart = datetime.now()
        game_id = game.gamestart.strftime('%y%j-%H%M%S')
        last_move = game.moves[-1]
        logger.info(f'{game_id} move: {last_move.move}')
        logger.info(f'{game_id} warp: {get_last_warp()}')
        logger.info(f'{game_id} player: {last_move.player}')
        logger.info(f'{game_id} coord: {last_move.coord} vertical: {last_move.is_vertical}')
        logger.info(f'{game_id} word: {last_move.points}')
        logger.info(f'{game_id} points: {last_move.points}')
        logger.info(f'{game_id} score: {last_move.score}')
        logger.info(f'{game_id} new tiles: {last_move.new_tiles}')
        logger.info(f'{game_id} removed tiles: {last_move.removed_tiles}')
        logger.info(f'{game_id} board: {last_move.board}')

    if config.is_testing:
        logging.info('Skip store because is_testing is set')
        return

    if move_to_store:
        if not only_json and move_to_store.img is not None:
            save_image(f'{config.path.web_dir}/image-{move_to_store.move}.jpg', move_to_store.img)
        if config.development.recording and dev_img is not None:
            save_image(f'{config.path.web_dir}/image-{move_to_store.move}-camera.jpg', dev_img)
            write_dev_log_entry()

        json_content = game.json_str(move_to_store.move)
        write_json_file(f'{config.path.web_dir}/data-{move_to_store.move}.json', json_content)
        if move_to_store.move == game.moves[-1].move:
            write_json_file(f'{config.path.web_dir}/status.json', json_content)
        if config.output.upload_server:
            upload_impl.last_future = pool.submit(upload.upload_move, upload_impl.last_future, move_to_store.move)
    else:
        json_content = game.json_str()
        write_json_file(f'{config.path.web_dir}/status.json', json_content)
        if config.output.upload_server:
            upload_impl.last_future = pool.submit(upload.upload_status, upload_impl.last_future)


def store_zip_from_game(game: Game):  # pragma: no cover
    """zip a game and upload to server"""
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
    with ZipFile(f'{config.path.web_dir}/{zip_filename}.zip', 'w') as _zip:
        logging.info(f'create zip with {len(game.moves):d} files')
        for mov in game.moves:
            if os.path.exists(f'{config.path.web_dir}/image-{mov.move}.jpg'):
                _zip.write(f'{config.path.web_dir}/image-{mov.move}.jpg', arcname=f'image-{mov.move}.jpg')
            if os.path.exists(f'{config.path.web_dir}/image-{mov.move}-camera.jpg'):
                _zip.write(f'{config.path.web_dir}/image-{mov.move}-camera.jpg', arcname=f'image-{mov.move}-camera.jpg')
            if os.path.exists(f'{config.path.web_dir}/data-{mov.move}.json'):
                _zip.write(f'{config.path.web_dir}/data-{mov.move}.json', arcname=f'data-{mov.move}.json')
        if os.path.exists(f'{config.path.log_dir}/messages.log'):
            _zip.write(f'{config.path.log_dir}/messages.log', arcname='messages.log')
        if os.path.exists(f'{config.path.log_dir}/gameRecording.log'):
            _zip.write(f'{config.path.log_dir}/gameRecording.log', arcname='gameRecording.log')

    if config.output.upload_server:
        upload_impl.last_future = pool.submit(upload.zip_files, upload_impl.last_future, f'{zip_filename}')
