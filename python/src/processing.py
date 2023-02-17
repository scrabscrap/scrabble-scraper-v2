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
from customboard import CustomBoard
from game_board.board import GRID_H, GRID_W, get_x_position, get_y_position
from game_board.tiles import tiles
from scrabble import Game, InvalidMoveExeption, Move, MoveType, NoMoveException
from threadpool import pool
from util import trace

Mat = np.ndarray[int, np.dtype[np.generic]]


def get_last_warp() -> Optional[Mat]:
    """Delegates the warp of the ``img`` according to the configured board style"""
    if config.video_warp and config.board_layout == 'classic':
        return ClassicBoard.last_warp
    return CustomBoard.last_warp


def clear_last_warp():
    """Delegates the warp of the ``img`` according to the configured board style"""
    if config.board_layout == 'classic':
        ClassicBoard.last_warp = None
    else:
        CustomBoard.last_warp = None


def warp_image(img: Mat) -> Mat:
    """Delegates the warp of the ``img`` according to the configured board style"""
    logging.debug(f'({config.board_layout})')
    if config.video_warp and config.board_layout == 'custom':
        return CustomBoard.warp(img)
    if config.video_warp and config.board_layout == 'classic':
        return ClassicBoard.warp(img)
    return img


def filter_image(img: Mat) -> tuple[Optional[Mat], set]:
    """Delegates the image filter of the ``img`` according to the configured board style"""
    logging.debug(f'({config.board_layout})')
    if config.board_layout == 'custom':
        return CustomBoard.filter_image(img)
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

    def find_tile(coord: tuple[int, int], gray: Mat, _board: dict):
        (col, row) = coord
        (tile, prop) = _board[coord] if coord in _board else ('_', 76)
        if prop > 90:
            logging.debug(f"{chr(ord('A') + row)}{col + 1:2}: {tile} ({prop}) tile on board prop > 90 ")
            return _board[coord]
        (tile, prop) = match(gray, tile, prop)
        if prop < 90:
            (tile, prop) = match(imutils.rotate(gray, -10), tile, prop)
        if prop < 90:
            (tile, prop) = match(imutils.rotate(gray, 10), tile, prop)
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


def recalculate_score_on_admin_change(game: Game, move_number: int, coord: Tuple[int, int], isvertical: bool, word: str):
    # pylint: disable=R0914, R0912
    """fix move (direct call from admin)

    The provided tiles (word) will be set on the board with a probability of 99%

    Args:
        game(Move): the game to fix
        move_number: the move to fix (beginning with 1)
        coord: coordinates on board (0<=col<15, 0<=row<15)
        isvertical: if this corrected move is vertical
        word: the new word valid chars (A-Z._) crossing chars will replaced with '.'
    """
    moves = game.moves
    if 0 < move_number <= len(moves):
        assert moves[move_number - 1].move == move_number
        assert 0 <= coord[0] < 15
        assert 0 <= coord[1] < 15

        index = move_number - 1
        assert moves[index].type == MoveType.REGULAR

        logging.debug(f'try to fix move {move_number} at {coord} vertical={isvertical} with {word}')
        board = moves[index].board.copy()

        tiles_to_remove = moves[index].new_tiles.copy()                        # tiles to delete
        for elem in tiles_to_remove:
            del board[elem]                                                    # remove tiles on board from incorrect move
        logging.debug(f'tiles_to_remove {tiles_to_remove}')
        tiles_to_add: dict = {}                                                # tiles to add
        (col, row) = coord
        for i, char in enumerate(word):
            if isvertical and char != '.' and (col, row + i) not in board:
                tiles_to_add[(col, row + i)] = (char, 99)
            elif char != '.' and (col + i, row) not in board:
                tiles_to_add[(col + i, row)] = (char, 99)
        logging.debug(f'tiles_to_add {tiles_to_add}')

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
            elif new_move.type == MoveType.EXCHANGE:
                if len(moves) > 1:
                    new_move.points = moves[i - 1].points
            else:
                new_move = _move_processing(game, new_move.player, new_move.played_time, new_move.img,
                                            new_move.board, previous_board, previous_score)
            new_move.move = i + 1
            previous_board = new_move.board
            previous_score = new_move.score
            moves[i] = new_move
            logging.info(f'recalculate move #{moves[i].move} ({moves[i].type})')
            logging.info(f'new points {moves[i].points} new score {moves[i].score}')
            logging.debug(f'\n{game.board_str(i)}')
            _store_fixed_move(game, moves[i])
            _upload_ftp(moves[i])
    else:
        raise ValueError("invalid move number")


@ trace
def move(waitfor: Optional[Future], game: Game, img: Mat, player: int, played_time: Tuple[int, int]):
    # pylint: disable=R0915,R0914
    """Process a move

    Args:
        waitfor (futures): wait for jobs to complete
        game(Game): the current game data
        img: the image to analyze
        player (int): active player
        played_time (int, int): current player times
    """
    warped, board = _image_processing(waitfor, game, img)

    previous_board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}   # get previous board information
    previous_score = game.moves[-1].score if len(game.moves) > 0 else (0, 0)

    current_move = _move_processing(game, player, played_time, warped, board, previous_board, previous_score)

    game.add_move(current_move)                                                # 9. add move
    if logging.getLogger('root').isEnabledFor(logging.DEBUG):
        msg = ''
        msg = f'game status: {game.json_str()}\n\nscores {game.moves[-1].score}\n'
        for i in range(0, len(game.moves)):
            msg += f'{game.moves[i].gcg_str(game.nicknames)}\n'
        msg += f'{game.board_str()}'
        logging.debug(msg)
    _development_recording(game, img, info=True)
    _store_move(game, warped)                                                  # 10. store move on hd
    _upload_ftp(current_move)


@ trace
def valid_challenge(waitfor: Optional[Future], game: Game, player: int, played_time: Tuple[int, int]):
    """Process a valid challenge

    Args:
        waitfor (futures): wait for jobs to complete
        game(Game): the current game data
        player (int): active player
        played_time (int, int): current player times
    """
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    game.add_valid_challenge(player, played_time)                              # 9. add move
    logging.debug(f'new scores {game.moves[-1].score}: {game.json_str()}\n{game.board_str()}')
    _development_recording(game, None, info=True)
    _store_move(game, None)                                                    # 10. store move on hd
    _upload_ftp(game.moves[-1])


@ trace
def invalid_challenge(waitfor: Optional[Future], game: Game, player: int, played_time: Tuple[int, int]):
    """Process an invalid challenge

    Args:
        waitfor (futures): wait for jobs to complete
        game(Game): the current game data
        player (int): active player
        played_time (int, int): current player times
    """
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    game.add_invalid_challenge(player, played_time)                            # 9. add move
    logging.debug(f'new scores {game.moves[-1].score}: {game.json_str()}\n{game.board_str()}')
    _development_recording(game, None, info=True)
    _store_move(game, None)                                                     # 10. store move on hd
    _upload_ftp(game.moves[-1])                                                 # 11. upload move to ftp


@ trace
def store_status(game: Game):
    """store current status.json - does not update data-*.json !"""
    from ftp import Ftp
    if config.output_web or config.output_ftp:
        with open(f'{config.web_dir}/status.json', "w", encoding='UTF-8') as handle:
            handle.write(game.json_str())
        pool.submit(Ftp.upload_status)                    # upload empty status


@ trace
def start_of_game(game: Game):
    """ start of game """
    from ftp import Ftp
    pool.submit(Ftp.delete_files, ['image', 'data'])  # first delete images and data files on ftp server
    store_status(game)


@ trace
def end_of_game(waitfor: Optional[Future], game: Game):  # pragma: no cover # no ftp upload on tests
    """Process end of game

    Args:
        waitfor (futures): wait for jobs to complete
        game(Game): the current game data
    """
    import glob
    import os
    import uuid
    from zipfile import ZipFile

    from ftp import Ftp

    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    # time.sleep(1.5)
    game_id = game.gamestart.strftime("%y%j-%H%M%S")  # type: ignore
    zip_filename = f'{game_id}-{str(uuid.uuid4())}'
    if config.output_web or config.output_ftp:
        with ZipFile(f'{config.web_dir}/{zip_filename}.zip', 'w') as _zip:
            logging.info(f"create zip with {len(game.moves):d} files")
            for i in range(1, len(game.moves) + 1):
                _zip.write(f'{config.web_dir}/image-{i}.jpg', arcname=f'image-{i}.jpg')
                _zip.write(f'{config.web_dir}/data-{i}.json', arcname=f'data-{i}.json')
            if os.path.exists(f'{config.log_dir}/messages.log'):
                _zip.write(f'{config.log_dir}/messages.log', arcname='messages.log')
            if config.development_recording:
                logging.debug('add development recording')
                file_list = glob.glob(f'{config.work_dir}/recording/{game_id}-*')
                for filename in file_list:
                    _zip.write(f'{filename}', arcname=os.path.basename(filename))
                if os.path.exists(f'{config.work_dir}/recording/gameRecording.log'):
                    _zip.write(f'{config.work_dir}/recording/gameRecording.log', arcname='gameRecording.log')

    if config.output_ftp:
        Ftp.upload_game(f'{zip_filename}')


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


def _development_recording(game: Game, img: Optional[Mat], suffix: str = '', info: bool = False):  # pragma: no cover
    # no dev recording on tests
    if config.development_recording:
        logging.debug(f'suffix "{suffix}" info {info}')
        recording_logger = logging.getLogger("gameRecordingLogger")
        game_id = game.gamestart.strftime("%y%j-%H%M%S")  # type: ignore
        if img is not None:
            move_number = len(game.moves)
            cv2.imwrite(f'{config.work_dir}/recording/{game_id}-{move_number}{suffix}.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 99])
        if info:
            warp_str = np.array2string(get_last_warp(), formatter={  # type: ignore
                'float_kind': lambda x: f'{x:.1f}'}, separator=',')
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
        (col, row) = changed[-1]
        horizontal = ((col - 1, row) in board) or ((col + 1, row) in board)
        vertical = ((col, row - 1) in board) or ((col, row + 1) in board) if not horizontal else False
    (col, row) = changed[0]
    (minx, miny) = changed[0]
    _word = ''
    if vertical:
        while row > 0 and (col, row - 1) in board:
            row -= 1
        miny = row
        while row < 15 and (col, row) in board:
            _word += board[(col, row)][0] if (col, row) in changed else '.'
            row += 1
    else:
        while col > 0 and (col - 1, row) in board:
            col -= 1
        minx = col
        while col < 15 and (col, row) in board:
            _word += board[(col, row)][0] if (col, row) in changed else '.'
            col += 1
    return vertical, (minx, miny), _word


def _image_processing(waitfor: Optional[Future], game: Game, img: Mat) -> Tuple[Mat, dict]:
    if waitfor is not None:                                                    # wait for previous moves
        done, not_done = futures.wait({waitfor})
        assert len(not_done) == 0, 'error while waiting for future'
    warped = warp_image(img)                                                   # 1. warp image if necessary
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)                     # 2. grayscale image
    filtered_image, tiles_candidates = filter_image(warped)                    # 3. find potential tiles on board
    _development_recording(game, filtered_image, suffix='~filter')

    if len(game.moves) > 1:                                                    # 3a. check for wrong blank tiles
        # TODO: extract this for testing
        to_del = [i for i in game.moves[-1].board.keys() if game.moves[-1].board[i][0] == '_' and i not in tiles_candidates]
        if to_del:
            _move = game.moves[-1]
            for i in to_del:
                logging.warning(f'remove blank tiles from the last move because they are no longer recognized {i}')
                del _move.board[i]
                del _move.new_tiles[i]
            logging.warning(f'try to recalculate move #{_move.move}')
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
        if game.moves[-config.scrabble_verify_moves + 1].type in (MoveType.PASS_TURN, MoveType.EXCHANGE, MoveType.WITHDRAW):
            ignore_coords = set(
                {i: i for i in game.moves[-config.scrabble_verify_moves + 1].board.keys() if i in game.moves[-1].board.keys()})
        else:
            ignore_coords = set(
                {i: i for i in game.moves[-config.scrabble_verify_moves].board.keys() if i in game.moves[-1].board.keys()})
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
    # pylint: disable=R0913
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
                            previous_score=previous_score)
    except InvalidMoveExeption:
        current_move = Move(MoveType.UNKNOWN, player=player, coord=(0, 0), is_vertical=True, word='', new_tiles=new_tiles,
                            removed_tiles=removed_tiles, board=current_board, played_time=played_time,
                            previous_score=previous_score)

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
    for i in range(to_inspect, 0):
        mov = game.moves[i]
        for coord in changed.keys():
            if coord in mov.board.keys():                                      # tiles on board are changed
                logging.info(f'need correction {mov.board[coord]} -> {changed[coord]} {mov.score}/{mov.points}')
                mov.board[coord] = changed[coord]
                must_recalculate = True
        if must_recalculate:
            _word = ''
            (col, row) = mov.coord
            for i, char in enumerate(mov.word):                                # fix mov.word
                if mov.is_vertical:
                    _word += board[(col, row + i)][0] if char != '.' else '.'
                else:
                    _word += board[(col + i, row)][0] if char != '.' else '.'
            mov.word = _word
            mov.points, prev_score, mov.is_scrabble = mov.calculate_score(prev_score)
            mov.score = prev_score                                             # store previous score
            logging.debug(f'move {mov.move} after recalculate {prev_score}')
        else:
            prev_score = mov.score                                             # store previous score
    return prev_score


def _store_fixed_move(game: Game, move_to_store: Move):
    if config.output_web or config.output_ftp:
        with open(f'{config.web_dir}/data-{move_to_store.move}.json', "w", encoding='UTF-8') as handle:
            handle.write(game.json_str(move_to_store.move))
        if len(game.moves) == move_to_store.move:
            with open(f'{config.web_dir}/status.json', "w", encoding='UTF-8') as handle:
                handle.write(game.json_str())


def _store_move(game: Game, img: Optional[Mat]):
    """store move to filesystem

    Args:
        current_move(Move): the current move
        img(Mat): current picture
    """
    if config.output_web or config.output_ftp:
        with open(f'{config.web_dir}/data-{game.moves[-1].move}.json', "w", encoding='UTF-8') as handle:
            handle.write(game.json_str())
        with open(f'{config.web_dir}/status.json', "w", encoding='UTF-8') as handle:
            handle.write(game.json_str())
        if img is None:
            import shutil
            shutil.copyfile(f'{config.web_dir}/image-{game.moves[-1].move - 1}.jpg',
                            f'{config.web_dir}/image-{game.moves[-1].move}.jpg')
        else:
            cv2.imwrite(f'{config.web_dir}/image-{game.moves[-1].move}.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 99])


def _upload_ftp(current_move: Move):  # pragma: no cover # no ftp upload on tests
    """upload move to ftp server

    Args:
        current_move(Move): the current move
    """
    from ftp import Ftp
    if config.output_ftp:
        # start thread for upload and return immediatly
        pool.submit(Ftp.upload_move, current_move.move)
