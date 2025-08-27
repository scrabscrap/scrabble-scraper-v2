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
from contextlib import suppress
from pathlib import Path
from threading import Event

import cv2
from cv2.typing import MatLike

from analyzer import MAX_TILE_PROB, analyze, filter_candidates
from config import config
from customboard import filter_image, warp_image
from move import gcg_to_coord
from scrabble import BoardType, Game, MoveType, Tile
from utils.threadpool import Command
from utils.upload import upload
from utils.util import handle_exceptions, rotate_logs, runtime_measure, trace

logger = logging.getLogger()


def event_set(event: Event | None) -> None:
    """set event and skips set if event is None. Informs the webservice about the end of the task"""
    if event is not None:
        event.set()


@handle_exceptions
def remove_blanko(game: Game, gcg_coord: str, event: Event | None = None) -> None:
    """remove blank"""

    logger.info(f'remove blanko {gcg_coord}')
    _, coord = gcg_to_coord(gcg_string=gcg_coord)
    game.remove_blank(coordinates=coord)
    event_set(event=event)


@handle_exceptions
def set_blankos(game: Game, gcg_coord: str, value: str, event: Event | None = None) -> None:
    """set (lower) char for blanko"""

    logger.info(f'set blanko {gcg_coord} to {value}')
    _, coord = gcg_to_coord(gcg_string=gcg_coord)
    game.replace_blank_with(coordinates=coord, char=value)
    event_set(event=event)


@handle_exceptions
def admin_insert_moves(game: Game, index: int, event: Event | None = None) -> None:
    """insert two exchange moves before move at index"""

    logger.info(f'insert before move index {index}')
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

    required_fields = all(x is not None for x in (coord, isvertical, word))
    if movetype == MoveType.REGULAR and required_fields:
        (dcol, drow) = (0, 1) if isvertical else (1, 0)
        m = game.moves[index]
        previous_board = m.previous_move.board if m.previous_move else {}
        new_tiles: BoardType = {}
        for ch in word:  # type:ignore # only new chars
            if coord not in previous_board:
                new_tiles[coord] = Tile(ch, MAX_TILE_PROB)  # type: ignore
            coord = (coord[0] + dcol, coord[1] + drow)  # type: ignore
        logger.debug(f'new tiles {index=} {new_tiles=}')
        game.change_move_at(index, movetype=movetype, new_tiles=new_tiles)
    elif movetype == MoveType.EXCHANGE:
        logger.debug(f'exchange {index=}')
        game.change_move_at(index=index, movetype=movetype)
    event_set(event=event)


@handle_exceptions
def admin_del_challenge(game: Game, index: int, event: Event | None = None) -> None:
    """delete challenge move index (index)"""

    logger.info(f'delete challenge at index {index}')
    game.remove_move_at(index)
    event_set(event=event)


@handle_exceptions
def admin_toggle_challenge_type(game: Game, index: int, event: Event | None = None) -> None:
    """toggle challenge type on move number"""

    logger.info(f'toggle challenge at index {index}')
    game.toggle_challenge_type(index)
    event_set(event=event)


@handle_exceptions
def admin_ins_challenge(game: Game, index: int, move_type: MoveType, event: Event | None = None) -> None:
    """insert invalid challenge or withdraw for move number"""

    logger.info(f'insert challenge {move_type.name} at index {index}')
    if move_type == MoveType.CHALLENGE_BONUS:
        game.add_challenge_for(index=index)
    elif move_type == MoveType.WITHDRAW:
        game.add_withdraw_for(index=index, img=game.moves[index].img)  # type: ignore
    event_set(event=event)


@runtime_measure
def _image_processing(game: Game, img: MatLike) -> tuple[MatLike, dict]:
    warped, warped_gray = warp_image(img)  # warp image if necessary
    _, tiles_candidates = filter_image(warped)  # find potential tiles on board

    if game.moves:
        game.moves[-1].cleanup_invalid_blanks(tiles_candidates=tiles_candidates)
    ignore_coords = game.get_coords_to_ignore()
    tiles_candidates |= ignore_coords  # tiles_candidates must contain ignored_coords
    tiles_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)  # remove all tiles without path from (7,7)

    board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}  # copy board for analyze
    return warped, analyze(warped_gray, board, tiles_candidates)  # analyze image


def _board_diff(board: BoardType, previous_board: BoardType) -> tuple[BoardType, BoardType, BoardType]:
    new_tiles = {i: board[i] for i in set(board.keys()).difference(previous_board)}
    removed_tiles = {i: previous_board[i] for i in set(previous_board.keys()).difference(board)}
    changed_tiles = {
        i: board[i]
        for i in previous_board
        if i not in removed_tiles and previous_board[i].letter != board[i].letter and previous_board[i].prob < board[i].prob
    }
    return new_tiles, removed_tiles, changed_tiles


def _move_processing(game: Game, board: BoardType, previous_board: BoardType) -> tuple[BoardType, BoardType, BoardType]:
    new_tiles, removed_tiles, changed_tiles = _board_diff(board, previous_board)  # find changes on board
    new_tiles = game.clean_new_tiles(new_tiles=new_tiles, previous_board=previous_board)
    return new_tiles, removed_tiles, changed_tiles


def _recalculate_score_on_tiles_change(game: Game, changed: BoardType) -> None:
    """fix scores on changed tiles after recognition"""

    logger.info(f'changed tiles: {changed}')
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
            logger.info(f'recalculated score: {str(mov)}')


def _write_original_image(img: MatLike, index: int) -> None:
    if config.development.recording:
        image_path = config.path.web_dir / f'image-{index}-camera.jpg'
        logger.debug(f'write image {image_path!s}')
        with suppress(Exception):
            cv2.imwrite(str(image_path), img, [cv2.IMWRITE_JPEG_QUALITY, 100])  # type:ignore


@trace
@handle_exceptions
def move(game: Game, img: MatLike, player: int, played_time: tuple[int, int], event: Event | None = None) -> None:
    """Process a move"""

    warped, board = _image_processing(game, img)

    previous_board = game.moves[-1].board.copy() if len(game.moves) > 0 else {}  # get previous board information
    new_tiles, removed_tiles, changed_tiles = _move_processing(game, board, previous_board)

    if len(changed_tiles) > 0:  # fix previous moves
        _recalculate_score_on_tiles_change(game, changed_tiles)
    if config.development.recording:  # save before upload
        index = len(game.moves)
        upload.get_upload_queue().put_nowait(Command(_write_original_image, img.copy(), index))
    game.add_move(player=player, played_time=played_time, img=warped, new_tiles=new_tiles, removed_tiles=removed_tiles)
    event_set(event)


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
            logger.info('automatic valid challenge after resume')
        # else: # uncomment if you want a invalid challenges as default on resume
        #     invalid_challenge(game, player, played_time, event)
        #     logger.info(f'automatic invalid challenge (move time {current_time[player]} sec)')


@trace
@handle_exceptions
def valid_challenge(game: Game, event: Event | None = None) -> None:
    """Process a valid challenge"""

    logger.info('add withdraw for last move')
    game.add_withdraw_for(index=-1, img=game.moves[-1].img)  # type: ignore
    logger.info(f'new scores {game.moves[-1].score}:\n{game.board_str()}')
    event_set(event=event)


@trace
@handle_exceptions
def invalid_challenge(game: Game, event: Event | None = None) -> None:
    """Process an invalid challenge"""

    logger.info('add challenge for last move')
    game.add_challenge_for()
    logger.info(f'new scores {game.moves[-1].score}:\n{game.board_str()}')
    event_set(event=event)


@trace
def new_game(game: Game, event: Event | None = None) -> None:
    """start of game"""

    if not config.is_testing:
        # first delete images and data files on ftp server
        if config.output.upload_server:
            upload.get_upload_queue().put_nowait(Command(upload.delete_files))
        with suppress(OSError):
            web_dir = Path(config.path.web_dir)
            file_list = list(web_dir.glob('image-*.jpg')) + list(web_dir.glob('data-*.json'))
            for file_path in file_list:
                file_path.unlink()
            if file_list:
                rotate_logs()
    game.new_game()
    event_set(event)


@trace
def end_of_game(game: Game, image: MatLike | None = None, player: int = -1, event: Event | None = None) -> None:
    # pragma: no cover
    """Process end of game"""

    if not game.moves:
        return
    prev_move = game.moves[-1]
    has_tiles = all(size > 0 for size in prev_move.rack_size[:2])

    if image is not None and has_tiles:  # we have an image and both racks have tiles
        last_move = game.moves[-1]
        warped, _ = warp_image(image)
        _, tiles_candidates = filter_image(warped)
        if set(last_move.board.keys()) != set(tiles_candidates):  #  candidates differ from last image
            logger.info(f'automatic move (player {player})')
            move(game, image, player, last_move.played_time, event)

    game.end_game()
    event_set(event)
