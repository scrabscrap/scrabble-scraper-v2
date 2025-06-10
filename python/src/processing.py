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
from contextlib import suppress
from threading import Event

import cv2
import imutils
from cv2.typing import MatLike

import upload_impl
from config import config
from custom2012board import Custom2012Board
from custom2020board import Custom2020Board
from custom2020light import Custom2020LightBoard
from game_board.board import GRID_H, GRID_W, get_x_position, get_y_position
from game_board.tiles import tiles
from scrabble import BoardType, Game, InvalidMoveError, MoveType, NoMoveError, Tile, gcg_to_coord
from threadpool import pool
from upload import upload
from util import TWarp, handle_exceptions, runtime_measure, trace

ANALYZE_THREADS = 4
BOARD_CLASSES = {'custom2012': Custom2012Board, 'custom2020': Custom2020Board, 'custom2020light': Custom2020LightBoard}
BLANK_PROP = 76
MAX_TILE_PROB = 99
MATCH_ROTATIONS = [0, -5, 5, -10, 10, -15, 15]
THRESHOLD_PROP_BOARD = 97
THRESHOLD_PROP_TILE = 86
THRESHOLD_UMLAUT_BONUS = 2
UMLAUTS = ('Ä', 'Ü', 'Ö')
ORD_A = ord('A')


def event_set(event: Event | None) -> None:
    """set event and skips set if event is None. Informs the webservice about the end of the task"""
    if event is not None:
        event.set()


def get_last_warp() -> TWarp | None:
    """Delegates the warp of the ``img`` according to the configured board style"""
    return BOARD_CLASSES.get(config.board.layout, Custom2012Board).last_warp


def clear_last_warp() -> None:
    """Delegates the last_warp according to the configured board style"""
    BOARD_CLASSES.get(config.board.layout, Custom2012Board).last_warp = None


@runtime_measure
def warp_image(img: MatLike) -> tuple[MatLike, MatLike]:
    """Delegates the warp of the ``img`` according to the configured board style"""
    warped = BOARD_CLASSES.get(config.board.layout, Custom2012Board).warp(img) if config.video.warp else img
    return warped, cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)


@runtime_measure
def filter_image(img: MatLike) -> tuple[MatLike | None, set]:
    """Delegates the image filter of the ``img`` according to the configured board style"""
    return BOARD_CLASSES.get(config.board.layout, Custom2012Board).filter_image(img)


DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


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
    return result


def analyze(warped_gray: MatLike, board: BoardType, coord_list: set[tuple[int, int]]) -> BoardType:
    """find tiles on board"""

    def match_tile(img: MatLike, suggest_tile: str, suggest_prop: int) -> Tile:
        for _tile in tiles:
            res = cv2.matchTemplate(img, _tile.img, cv2.TM_CCOEFF_NORMED)
            _, thresh, _, _ = cv2.minMaxLoc(res)
            thresh = int(thresh * 100)
            if _tile.name in UMLAUTS and thresh > suggest_prop - THRESHOLD_UMLAUT_BONUS:
                thresh = min(MAX_TILE_PROB, thresh + THRESHOLD_UMLAUT_BONUS)  # 2% Bonus for umlauts
                logging.debug(f'{chr(ORD_A + row)}{col + 1:2} => ({_tile.name},{thresh}) increased prop')
            if thresh > suggest_prop:
                suggest_tile, suggest_prop = _tile.name, thresh
        return Tile(letter=suggest_tile, prob=suggest_prop)

    def find_tile(gray: MatLike, tile: Tile) -> Tile:
        if tile.prob > THRESHOLD_PROP_BOARD:
            logging.debug(f'{chr(ORD_A + row)}{col + 1:2}: {tile} ({tile.prob}) tile on board prop > {THRESHOLD_PROP_BOARD} ')
            return tile

        for angle in MATCH_ROTATIONS:
            tile = match_tile(imutils.rotate(gray, angle), tile.letter, tile.prob)
            if tile.prob >= config.board.min_tiles_rate:
                break

        return tile if tile is not None and tile.prob > THRESHOLD_PROP_TILE else Tile('_', BLANK_PROP)

    for coord in coord_list:
        (col, row) = coord
        x, y = get_x_position(col), get_y_position(row)
        segment = warped_gray[y - 15 : y + GRID_H + 15, x - 15 : x + GRID_W + 15]
        board[coord] = find_tile(segment, board.get(coord, Tile('_', BLANK_PROP)))
        logging.info(f'{chr(ORD_A + row)}{col + 1:2}: {board[coord]}) found')
    return board


def analyze_threads(warped_gray: MatLike, board: BoardType, candidates: set[tuple[int, int]]) -> BoardType:
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


@handle_exceptions
def remove_blanko(game: Game, gcg_coord: str, event: Event | None = None) -> None:
    """remove blank"""

    logging.info(f'remove blanko {gcg_coord}')
    _, coord = gcg_to_coord(gcg_string=gcg_coord)
    game.remove_blank(coordinates=coord)
    event_set(event=event)


@handle_exceptions
def set_blankos(game: Game, gcg_coord: str, value: str, event: Event | None = None) -> None:
    """set (lower) char for blanko"""

    logging.info(f'set blanko {gcg_coord} to {value}')
    _, coord = gcg_to_coord(gcg_string=gcg_coord)
    game.replace_blank_with(coordinates=coord, char=value)
    event_set(event=event)


@handle_exceptions
def admin_insert_moves(game: Game, index: int, event: Event | None = None) -> None:
    """insert two exchange moves before move at index"""

    logging.info(f'insert before move index {index}')
    game.add_two_exchanges_at(index)
    event_set(event=event)


@handle_exceptions
def admin_change_move(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    game: Game,
    index: int,
    movetype: MoveType,
    coord: tuple[int, int] | None = None,
    isvertical: bool | None = None,
    word: str | None = None,
    event: Event | None = None,
) -> None:
    """fix move(direct call from admin)
    The provided tiles(word) will be set on the board with a probability of 99% (MAX_TILE_PROB)
    """

    if movetype == MoveType.REGULAR and coord is not None and isvertical is not None and word is not None:
        (dcol, drow) = (0, 1) if isvertical else (1, 0)
        m = game.moves[index]
        previous_board = m.previous_move.board if m.previous_move else {}
        new_tiles: BoardType = {}
        for ch in word:  # only new chars
            if coord not in previous_board:
                new_tiles[coord] = Tile(ch, MAX_TILE_PROB)
            coord = (coord[0] + dcol, coord[1] + drow)
        logging.debug(f'new tiles {index=} {new_tiles=}')
        game.change_move_at(index, movetype=movetype, new_tiles=new_tiles)
    elif movetype == MoveType.EXCHANGE:
        logging.debug(f'exchange {index=}')
        game.change_move_at(index=index, movetype=movetype)
    event_set(event=event)


@handle_exceptions
def admin_del_challenge(game: Game, index: int, event: Event | None = None) -> None:
    """delete challenge move index (index)"""

    logging.info(f'delete challenge at index {index}')
    game.remove_move_at(index)
    event_set(event=event)


@handle_exceptions
def admin_toggle_challenge_type(game: Game, index: int, event: Event | None = None) -> None:
    """toggle challenge type on move number"""

    logging.info(f'toggle challenge at index {index}')
    game.toggle_challenge_type(index)
    event_set(event=event)


@handle_exceptions
def admin_ins_challenge(game: Game, index: int, move_type: MoveType, event: Event | None = None) -> None:
    """insert invalid challenge or withdraw for move number"""

    logging.info(f'insert challenge at index {index}')
    previous_move = game.moves[index].previous_move
    if previous_move and move_type == MoveType.CHALLENGE_BONUS:
        game.add_challenge_for(index=index)
    elif previous_move and move_type == MoveType.WITHDRAW:
        game.add_withdraw_for(index=index, img=previous_move.img)  # type: ignore
    event_set(event=event)


@runtime_measure
def _image_processing(game: Game, img: MatLike) -> tuple[MatLike, dict]:
    warped, warped_gray = warp_image(img)  # warp image if necessary
    _, tiles_candidates = filter_image(warped)  # find potential tiles on board

    if game.moves:
        prev_move = game.moves[-1]  # remove invalid blanks
        blanks_to_remove = [i for i in prev_move.new_tiles if (prev_move.board[i].letter == '_') and i not in tiles_candidates]
        for to_del in blanks_to_remove:
            del prev_move.new_tiles[to_del]
        if blanks_to_remove:
            prev_move.calculate_score()  # catch exception NoMoveException, InvalidMoveException
        to_verify = min(len(game.moves), config.scrabble.verify_moves)  # find keys to ignore on analyze
        ignore_coords = set(game.moves[-to_verify].board.keys())
    else:
        ignore_coords = set()
    tiles_candidates |= ignore_coords  # tiles_candidates must contain ignored_coords
    tiles_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)  # remove all tiles without path from (7,7)
    logging.debug(f'filtered_candidates {tiles_candidates}')

    board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}  # copy board for analyze
    return warped, analyze_threads(warped_gray, board, tiles_candidates)  # analyze image


def _changes(board: dict, previous_board: dict) -> tuple[dict, dict, dict]:
    new_tiles = {i: board[i] for i in set(board.keys()).difference(previous_board)}
    removed_tiles = {i: previous_board[i] for i in set(previous_board.keys()).difference(board)}
    changed_tiles = {
        i: board[i] for i in previous_board if i not in removed_tiles and previous_board[i].letter != board[i].letter
    }
    return new_tiles, removed_tiles, changed_tiles


def _move_processing(board: BoardType, previous_board: BoardType) -> tuple[BoardType, BoardType, BoardType]:
    # pylint: disable=too-many-branches

    def strip_invalid_blanks(current_board: BoardType, new_tiles: BoardType):
        blanks = {(col, row) for col, row in new_tiles if new_tiles[(col, row)].letter == '_'}
        if not blanks:  # no blanks; skip
            return current_board, new_tiles

        previous_tiles = new_tiles.copy()
        set_of_cols = {col for col, row in new_tiles if new_tiles[(col, row)].letter != '_'}  # cols tiles with character
        set_of_rows = {row for col, row in new_tiles if new_tiles[(col, row)].letter != '_'}  # rows tiles with character

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

    new_tiles, removed_tiles, changed_tiles = _changes(board, previous_board)  # find changes on board
    _, new_tiles = strip_invalid_blanks(current_board=board, new_tiles=new_tiles)
    return new_tiles, removed_tiles, changed_tiles


def _recalculate_score_on_tiles_change(game: Game, changed: BoardType) -> None:
    """fix scores on changed tiles after recognition"""

    logging.info(f'changed tiles: {changed}')
    to_inspect = min(config.scrabble.verify_moves, len(game.moves))
    must_recalculate = False
    for mov in game.moves[-to_inspect:]:
        for coord in changed:
            if coord in mov.new_tiles:
                mov.new_tiles[coord] = changed[coord]
                must_recalculate = True
        if must_recalculate:
            mov.setup_board()
            mov.calculate_score()
            logging.info(f'recalculated score: {str(mov)}')


@trace
@handle_exceptions
def move(game: Game, img: MatLike, player: int, played_time: tuple[int, int], event: Event | None = None) -> None:
    """Process a move"""

    warped, board = _image_processing(game, img)

    previous_board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}  # get previous board information
    new_tiles, removed_tiles, changed_tiles = _move_processing(board, previous_board)

    if len(changed_tiles) > 0:  # fix previous moves
        _recalculate_score_on_tiles_change(game, changed_tiles)
    try:
        game.add_regular(player=player, played_time=played_time, img=warped, new_tiles=new_tiles)
    except NoMoveError:
        game.add_exchange(player=player, played_time=played_time, img=warped)
    except InvalidMoveError:
        game.add_unknown(player=player, played_time=played_time, img=warped, new_tiles=new_tiles, removed_tiles=removed_tiles)
    event_set(event)

    logging.info(f'new scores {game.moves[-1].score}:\n{game.board_str()}')
    if logging.getLogger('root').isEnabledFor(logging.DEBUG):
        msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in game.moves)
        json_str = game.json_str()
        logging.debug(f'{msg}\napi: {json_str[: json_str.find("moves") + 7]}...\n')


@trace
def check_resume(game: Game, image: MatLike, event: Event | None = None) -> None:
    """check resume"""

    last_move = game.moves[-1] if game.moves else None
    if last_move is not None and last_move.type == MoveType.REGULAR:  # only check regular moves
        if not last_move.new_tiles:  # no new tiles in last move
            return
        warped, _ = warp_image(image)
        _, tiles_candidates = filter_image(warped)
        intersection = set(last_move.new_tiles.keys()) & set(tiles_candidates)
        if intersection == set():  #  empty set => tiles are removed
            valid_challenge(game, event)
            logging.info('automatic valid challenge after resume')
            event_set(event=event)
        # else: # uncomment if you want a invalid challenges as default on resume
        #     invalid_challenge(game, player, played_time, event)
        #     logging.info(f'automatic invalid challenge (move time {current_time[player]} sec)')


@trace
@handle_exceptions
def valid_challenge(game: Game, event: Event | None = None) -> None:
    """Process a valid challenge"""

    logging.info('add withdraw for last move')
    game.add_withdraw_for(index=-1, img=game.moves[-1].img)  # type: ignore
    logging.info(f'new scores {game.moves[-1].score}:\n{game.board_str()}')
    event_set(event=event)


@trace
@handle_exceptions
def invalid_challenge(game: Game, event: Event | None = None) -> None:
    """Process an invalid challenge"""

    logging.info('add challenge for last move')
    game.add_challenge_for()
    logging.info(f'new scores {game.moves[-1].score}:\n{game.board_str()}')
    event_set(event=event)


@trace
def new_game(game: Game, event: Event | None = None) -> None:
    """start of game"""
    import glob
    import os

    import util

    if not config.is_testing:
        # first delete images and data files on ftp server
        upload_impl.last_future = pool.submit(upload.delete_files, upload_impl.last_future)
        with suppress(OSError):
            file_list = glob.glob(f'{config.path.web_dir}/image-*.jpg')
            file_list += glob.glob(f'{config.path.web_dir}/data-*.json')
            for file_path in file_list:
                os.remove(file_path)
            if file_list:
                util.rotate_logs()
    game.new_game()
    event_set(event)


@trace
def end_of_game(game: Game, image: MatLike | None = None, player: int = -1, event: Event | None = None) -> None:
    # pragma: no cover
    """Process end of game"""

    if game.moves:  # check for a last move on end of game
        prev_move = game.moves[-1]
        if (
            image is not None and prev_move.rack_size[0] > 0 and prev_move.rack_size[1] > 0
        ):  # we have an image and both racks have tiles
            last_move = game.moves[-1]
            warped, _ = warp_image(image)
            _, tiles_candidates = filter_image(warped)
            if set(last_move.board.keys()) != set(tiles_candidates):  #  candidates differ from last image
                logging.info(f'automatic move (player {player})')
                move(game, image, player, last_move.played_time, event)

        game.add_timeout_malus()  # add as move
        game.add_lastrack()
        event_set(event)

        logging.info(f'new scores {game.moves[-1].score}:\n{game.board_str()}')
        if logging.getLogger('root').isEnabledFor(logging.DEBUG):
            msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in game.moves)
            json_str = game.json_str()
            logging.debug(f'{msg}\napi: {json_str[: json_str.find("moves") + 7]}...\n')
        logging.info(game.dev_str())
        with suppress(Exception):
            store_zip_from_game(game)


def store_zip_from_game(game: Game) -> None:  # pragma: no cover
    """zip a game and upload to server"""
    import uuid
    from pathlib import Path
    from zipfile import ZipFile

    if config.is_testing:
        logging.info('skip store because flag is_testing is set')
        return
    game_id = game.gamestart.strftime('%y%j-%H%M%S')
    zip_filename = f'{game_id}-{str(uuid.uuid4())}'
    web_dir = Path(config.path.web_dir)
    log_dir = Path(config.path.log_dir)
    with ZipFile(web_dir / f'{zip_filename}.zip', 'w') as _zip:
        logging.info(f'create zip with {len(game.moves):d} files')
        for mov in game.moves:
            for suffix in ['.jpg', '-camera.jpg', '.json']:
                filename = f'{"image" if "jpg" in suffix else "data"}-{mov.move}{suffix}'
                filepath = web_dir / filename
                if filepath.exists():
                    _zip.write(filepath, arcname=filename)
        for log_file in ['messages.log', 'gameRecording.log']:
            log_path = log_dir / log_file
            if log_path.exists():
                _zip.write(log_path, arcname=log_file)
    if config.output.upload_server:
        upload_impl.last_future = pool.submit(upload.zip_files, upload_impl.last_future, f'{zip_filename}')
