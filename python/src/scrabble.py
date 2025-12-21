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

import json
import logging
import pprint
import time
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

import cv2
from cv2.typing import MatLike

from config import config, version
from move import (
    MAX_TILE_PROB,
    BoardType,
    CoordType,
    InvalidMoveError,
    Move,
    MoveChallenge,
    MoveExchange,
    MoveLastRackBonus,
    MoveLastRackMalus,
    MoveRegular,
    MoveTimeMalus,
    MoveType,
    MoveUnknown,
    MoveWithdraw,
    NoMoveError,
    Tile,
    bag_as_list,
)
from utils.threadpool import Command
from utils.upload import upload

API_VERSION = '3.2'
JSON_FLAG = 'json'
IMAGE_FLAG = 'image'
logger = logging.getLogger()


def board_to_string(board: BoardType) -> str:
    """Print out Scrabble board dictionary"""
    result = '\n  |' + ' '.join(f'{i + 1:2d}' for i in range(15)) + ' | ' + ' '.join(f'{i + 1:2d}' for i in range(15)) + '\n'
    for row in range(15):
        left = f'{chr(ord("A") + row)} |'
        right = '| '
        for col in range(15):
            cell_value = board.get((col, row), None)
            left += f' {cell_value.letter} ' if cell_value else ' . '
            right += f' {cell_value.prob}' if cell_value else ' . '
        result += left + right + ' | \n'
    return result


@dataclass(kw_only=True)
class Game:  # pylint: disable=too-many-public-methods
    """Represents the current game"""

    nicknames: tuple[str, str] = ('Name1', 'Name2')
    gamestart: datetime = field(default_factory=datetime.now)
    moves: list[Move] = field(default_factory=list)

    def __str__(self) -> str:
        return self.json_str()

    def _cell_name(self, coord: tuple[int, int]) -> str:
        return chr(ord('A') + coord[1]) + str(coord[0] + 1)  # pylint: disable=unnecessary-lambda-assignment

    def _build_base_data(self) -> dict:
        name1, name2 = self.nicknames
        return {
            'api': API_VERSION,
            'state': 'START',
            'timestamp': time.time(),
            'commit': version.git_commit,
            'layout': config.board.layout,
            'tournament': config.scrabble.tournament,
            'name1': name1, 'name2': name2, 'onmove': name1,
            'unknown_move': False,
            'time': str(self.gamestart),
            'move': 0,
            'score1': 0, 'score2': 0,
            'clock1': 0, 'clock2': 0,
            'time1': config.scrabble.max_time, 'time2': config.scrabble.max_time,
            'image': '',
            'moves': [],
            'moves_data': [],
            'board': {},
            'bag': self.tiles_in_bag(),
            'blankos': [],
        }  # fmt: off

    def _resolve_move_index(self, index: int) -> int:
        return len(self.moves) + index if index < 0 else index

    def _build_move_data(self, move_index: int, move: Move) -> dict:
        return {
            'onmove': self.nicknames[move.player],
            'state': self._determine_state(move),
            'unknown_move': self._has_unknown_move(move_index),
            'time': move.time,
            'move': move.move,
            'score1': move.score[0], 'score2': move.score[1],
            'clock1': config.scrabble.max_time - move.played_time[0],
            'clock2': config.scrabble.max_time - move.played_time[1],
            'time1': config.scrabble.max_time - move.played_time[0],
            'time2': config.scrabble.max_time - move.played_time[1],
            'image': f'web/image-{move_index}.jpg',
            'moves': [m.gcg_str for m in self.moves[: move_index + 1]],
            'moves_data': [self._serialize_move(m) for m in self.moves[: move_index + 1]],
            'board': {chr(ord('a') + y) + str(x + 1): tile.letter for (x, y), tile in move.board.items()},
            'blankos': self._collect_blankos(),
        }  # fmt: off

    def _determine_state(self, move: Move) -> str:
        if move.type in (MoveType.LAST_RACK_BONUS, MoveType.LAST_RACK_MALUS, MoveType.TIME_MALUS):
            return 'EOG'
        if move.type in (MoveType.REGULAR, MoveType.EXCHANGE, MoveType.PASS_TURN, MoveType.UNKNOWN, MoveType.WITHDRAW):
            return f'S{abs(move.player - 1)}'  # next move by the opponent
        return f'S{move.player}'

    def _has_unknown_move(self, move_index: int) -> bool:
        return 'MoveUnknown' in {x.__class__.__name__ for x in self.moves[: move_index + 1]}

    def _serialize_move(self, m: Move) -> dict:
        return {
            'move_type': m.type.name,
            'player': m.player,
            'start': m.gcg_coord.strip(),
            'word': m.calculate_word(),
            'gcg_word': m.gcg_word,  # type: ignore
            'new_letter': {chr(ord('a') + y) + str(x + 1): tile.letter for (x, y), tile in m.new_tiles.items()},
            'points': m.points,
            'score': m.score,
        }

    def _collect_blankos(self) -> list[tuple[str, str]]:
        return [
            (self._cell_name(key), tile.letter)
            for key, tile in self.moves[-1].board.items()
            if tile.letter.islower() or tile.letter == '_'
        ]

    def get_json_data(self, index: int = -1) -> dict:
        """Return the json representation of the board"""
        data = self._build_base_data()

        if not self.moves:
            return data

        move_index = self._resolve_move_index(index)
        move = self.moves[move_index]

        data |= self._build_move_data(move_index, move)

        return data

    def json_str(self, index: int = -1) -> str:
        """Return the json represention of the board"""
        return json.dumps(self.get_json_data(index=index), indent=2)  # Add indent here

    def valid_index(self, index: int) -> bool:
        """is (index) valid"""
        return bool(self.moves) and -len(self.moves) <= index < len(self.moves)

    def dev_str(self) -> str:  # pragma: no cover
        """Return development represention of the game for using in tests"""
        if self.gamestart is None:
            self.gamestart = datetime.now()
        game_id = self.gamestart.strftime('%y%j-%H%M%S')
        out_str = (
            f'game: {game_id}\ngame.ini\n'
            '[default]\n'
            f'warp = {config.video.warp}\n'
            f'name1 = {self.nicknames[0]}\n'
            f'name2 = {self.nicknames[1]}\n'
            f'formatter = image-{{:d}}.jpg\n'
            f'layout = {config.board.layout}\n'
        )
        if self.moves:
            out_str += ('start = Red\n', 'start = Green\n')[self.moves[0].player]
        if config.video.warp_coordinates:
            out_str += f'warp-coord = {config.video.warp_coordinates}\n'

        out_str += '\ngame.csv\n'
        out_str += 'Move, Button, State, Coord, Word, Points, Score1, Score2\n'
        for m in self.moves:
            out_str += m.dev_str + '\n'
        return out_str

    def board_str(self, index: int = -1) -> str:
        """Return the textual represention of the board"""
        if index > len(self.moves):
            return ''
        return board_to_string(board=self.moves[index].board)

    def set_player_names(self, name1: str, name2: str) -> None:
        """set player names"""
        logger.info(f"Setting player names to: '{name1}' and '{name2}'")
        self.nicknames = (name1, name2)
        self._write_json_from(index=-1, write_mode=[])  # only status file

    def new_game(self) -> Game:
        """Reset to a new game (nicknames, moves)"""
        logger.info('New game started')
        self.nicknames = ('Name1', 'Name2')
        self.gamestart = datetime.now()
        self.moves.clear()
        self._write_json_from(-1, [])
        return self

    def end_game(self) -> Game:
        """finish game"""
        logger.info('End of game started')
        self.add_timeout_malus()
        self.add_lastrack()

        upload.get_upload_queue().put_nowait(Command(self._zip_from_game))
        if config.output.upload_server:
            fname = (self.nicknames[0] + '-' + self.nicknames[1]).replace(' ', '_')
            logger.debug(f'{fname=}')
            upload.get_upload_queue().put_nowait(Command(upload.zip_files, fname))

        logger.info(f'final scores {self.moves[-1].score}\n{self.board_str()}')
        if logger.isEnabledFor(logging.DEBUG):
            msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in self.moves)
            pp = pprint.PrettyPrinter(indent=2, depth=1)
            logger.debug(f'{msg}\napi:\n{pp.pformat(self.get_json_data())}')  # pylint: disable=protected-access # noqa: SLF001
        logger.info(self.dev_str())
        upload.get_upload_queue().join()  # wait for finishing uploads

        return self

    def tiles_in_bag(self, index: int = -1) -> list[str]:
        """returns list of tiles in bag"""
        tiles_on_board = self.moves[index].board.values() if self.moves else []
        values = ['_' if tile.letter.isalpha() and tile.letter.islower() else tile.letter for tile in tiles_on_board]
        bag_counter = Counter(bag_as_list)
        for i in values:
            if bag_counter[i] > 0:
                bag_counter[i] -= 1
        result = []
        for k, v in bag_counter.items():
            result.extend([k] * v)
        return result

    def get_coords_to_ignore(self) -> set[tuple[int, int]]:
        """Returns the coordinates that are to be ignored in the analysis."""
        if not self.moves:
            return set()
        if len(self.moves) < config.scrabble.verify_moves:
            return set()
        return set(self.moves[-config.scrabble.verify_moves].board.keys()) & set(self.moves[-1].board.keys())

    def _recalculate_from(self, index: int) -> Game:
        """recalculate all moves from index"""
        for m in self.moves[index:]:
            m.setup_board()
            if isinstance(m, MoveRegular):
                m.calculate_coord()
            m.calculate_score()
        return self

    def _update_technical_move_attributes(self) -> Game:
        """update technical attributes in moves"""
        prev_move = None
        for i, m in enumerate(self.moves):
            m.move = i
            m.previous_move = prev_move
            prev_move = m
        return self

    def _write_image(self, index: int, web_dir: Path) -> None:
        img = self.moves[index].img
        if img is not None:
            image_path = web_dir / f'image-{index}.jpg'
            try:
                cv2.imwrite(str(image_path), img, [cv2.IMWRITE_JPEG_QUALITY, 100])  # type:ignore
            except Exception:
                logger.exception(f'Failed to write image {image_path}')

    def _write_json(self, index: int, web_dir: Path, fname: str) -> None:
        status_path = web_dir / fname
        try:
            with status_path.open('w', encoding='utf-8') as json_file:
                json.dump(self.get_json_data(index=index), json_file, indent=2)
        except OSError:
            logger.exception(f'Failed to write status file: {status_path}')

    def _write_json_from(self, index: int, write_mode: list[str]) -> Game:
        """Write JSON and images for moves starting from index."""
        if config.is_testing:
            return self

        web_dir = Path(config.path.web_dir)

        if not self.moves:
            self._enqueue_status_only(index, web_dir)
            return self

        index = index % len(self.moves)
        if not self.valid_index(index):
            logger.warning(f'invalid index {index} skipped')
            return self

        self._enqueue_writes(index, write_mode, web_dir)
        return self

    def _enqueue_status_only(self, index: int, web_dir: Path) -> None:
        """Handle case with no moves – only status.json upload."""
        upload.get_upload_queue().put_nowait(Command(self._write_json, -1, web_dir, 'status.json'))
        if config.output.upload_server:
            upload.get_upload_queue().put_nowait(Command(upload.upload_move, index))

    def _enqueue_writes(self, start_index: int, write_mode: list[str], web_dir: Path) -> None:
        """Enqueue write and upload tasks for all moves starting from index."""
        write_json = JSON_FLAG in write_mode
        write_img = IMAGE_FLAG in write_mode

        for i in range(start_index, len(self.moves)):
            if write_json:
                upload.get_upload_queue().put_nowait(Command(self._write_json, i, web_dir, f'data-{i}.json'))
            if write_img:
                upload.get_upload_queue().put_nowait(Command(self._write_image, i, web_dir))
            if i == len(self.moves) - 1:
                upload.get_upload_queue().put_nowait(Command(self._write_json, i, web_dir, 'status.json'))
            if config.output.upload_server:
                upload.get_upload_queue().put_nowait(Command(upload.upload_move, i))

    def _zip_from_game(self):
        if config.is_testing:
            logger.info('skip store because flag is_testing is set')
            return
        game_id = self.gamestart.strftime('%y%j-%H%M%S')
        zip_filename = f'{game_id}-{self.nicknames[0]}-{self.nicknames[1]}-{hex(int(time.time()))}'
        web_dir = config.path.web_dir
        log_dir = config.path.log_dir
        try:
            with ZipFile(web_dir / f'{zip_filename}.zip', 'w') as _zip:
                logger.info(f'create zip with {len(self.moves):d} files')
                for mov in self.moves:
                    for suffix in ['.jpg', '-camera.jpg', '.json']:
                        filename = f'{"image" if "jpg" in suffix else "data"}-{mov.move}{suffix}'
                        filepath = web_dir / filename
                        if filepath.exists():
                            _zip.write(filepath, arcname=filename)
                for log_file in ['game.log', 'messages.log']:
                    log_path = log_dir / log_file
                    if log_path.exists():
                        _zip.write(log_path, arcname=log_file)
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception('creating zip file failed')

    def _insert_move(self, move: Move, index: int = -1, recalc_from: int | None = None) -> Game:
        if index == -1:
            self.moves.append(move)
        else:
            self.moves.insert(index, move)
        self._update_technical_move_attributes()
        if recalc_from is not None:
            self._recalculate_from(recalc_from)
        logger.info(f'#{move.move}: {str(move)}')
        self._write_json_from(index=(index if index != -1 else len(self.moves) - 1), write_mode=[JSON_FLAG, IMAGE_FLAG])
        return self

    def clean_new_tiles(self, new_tiles: BoardType, previous_board: BoardType) -> BoardType:
        """
        Validates new tiles, especially blanks, against the Scrabble rules,
        by removing invalidly placed blank tiles that are not part
        of a connected move.
        """
        if not new_tiles:
            return {}

        real_tile_coords, blank_coords = self._split_tiles(new_tiles)

        if not blank_coords:
            return new_tiles

        if not real_tile_coords:
            return self._only_first_blank(blank_coords, new_tiles)

        direction = self._get_move_direction(real_tile_coords)
        if direction is None:
            return new_tiles

        full_board_coords = previous_board.keys() | new_tiles.keys()
        valid_blanks = self._find_valid_blanks(direction, blank_coords, real_tile_coords, full_board_coords)

        cleaned_new_tiles = {coord: new_tiles[coord] for coord in real_tile_coords}
        for coord in valid_blanks:
            cleaned_new_tiles[coord] = new_tiles[coord]

        self._log_removed_blanks(new_tiles, cleaned_new_tiles)
        return cleaned_new_tiles

    def _split_tiles(self, new_tiles: BoardType) -> tuple[set[CoordType], set[CoordType]]:
        real_tile_coords = {coord for coord, tile in new_tiles.items() if tile.letter != '_'}
        blank_coords = {coord for coord, tile in new_tiles.items() if tile.letter == '_'}
        return real_tile_coords, blank_coords

    def _only_first_blank(self, blank_coords: set[CoordType], new_tiles: BoardType) -> BoardType:
        first_blank = next(iter(blank_coords))
        return {first_blank: new_tiles[first_blank]}

    def _get_move_direction(self, real_tile_coords: set[CoordType]) -> str | None:
        cols = {c for c, r in real_tile_coords}
        rows = {r for c, r in real_tile_coords}
        if len(rows) == 1 and len(cols) > 0:
            return 'horizontal'
        if len(cols) == 1 and len(rows) > 0:
            return 'vertical'
        return None

    def _find_valid_blanks(
        self, direction: str, blank_coords: set[CoordType], real_tile_coords: set[CoordType], full_board_coords: set[CoordType]
    ) -> set[CoordType]:
        if len(real_tile_coords) <= 1:
            return self._find_valid_horizontal_blanks(
                blank_coords, real_tile_coords, full_board_coords
            ) | self._find_valid_vertical_blanks(blank_coords, real_tile_coords, full_board_coords)
        if direction == 'horizontal':
            return self._find_valid_horizontal_blanks(blank_coords, real_tile_coords, full_board_coords)
        return self._find_valid_vertical_blanks(blank_coords, real_tile_coords, full_board_coords)

    def _log_removed_blanks(self, new_tiles: BoardType, cleaned_new_tiles: BoardType) -> None:
        if len(cleaned_new_tiles) < len(new_tiles):
            removed = new_tiles.keys() - cleaned_new_tiles.keys()
            logger.info(f'removed blankos: {removed}')

    def _find_valid_horizontal_blanks(
        self, blank_coords: set[CoordType], real_tile_coords: set[CoordType], full_board_coords: set[CoordType]
    ) -> set[CoordType]:
        move_row = next(iter({r for c, r in real_tile_coords}))
        cols = [c for c, r in real_tile_coords]
        min_col, max_col = min(cols), max(cols)
        valid_blanks = set()
        for b_col, b_row in (b for b in blank_coords if b[1] == move_row):
            if all((c, move_row) in full_board_coords for c in range(min(b_col, min_col), max(b_col, max_col) + 1)):
                valid_blanks.add((b_col, b_row))
        return valid_blanks

    def _find_valid_vertical_blanks(
        self, blank_coords: set[CoordType], real_tile_coords: set[CoordType], full_board_coords: set[CoordType]
    ) -> set[CoordType]:
        move_col = next(iter({c for c, r in real_tile_coords}))
        rows = [r for c, r in real_tile_coords]
        min_row, max_row = min(rows), max(rows)
        valid_blanks = set()
        for b_col, b_row in (b for b in blank_coords if b[0] == move_col):
            if all((move_col, r) in full_board_coords for r in range(min(b_row, min_row), max(b_row, max_row) + 1)):
                valid_blanks.add((b_col, b_row))
        return valid_blanks

    def add_move(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, player: int, played_time: tuple[int, int], img: MatLike, new_tiles: BoardType, removed_tiles: BoardType
    ) -> Game:
        """Adds a new move and determines the type automatically."""
        try:
            self.add_regular(player, played_time, img, new_tiles)
        except NoMoveError:
            self.add_exchange(player, played_time, img)
        except InvalidMoveError:
            self.add_unknown(player, played_time, img, new_tiles, removed_tiles)
        logger.info(f'Scores after move #{self.moves[-1].move} {self.moves[-1].score}\n{self.board_str()}')
        if logger.isEnabledFor(logging.DEBUG):
            msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in self.moves)
            pp = pprint.PrettyPrinter(indent=2, depth=1)
            logger.debug(f'{msg}\napi:\n{pp.pformat(self.get_json_data())}')

        return self

    def add_regular(self, player: int, played_time: tuple[int, int], img: MatLike, new_tiles: BoardType) -> Game:
        """add regular move"""
        prev_move = self.moves[-1] if self.moves else None
        m = MoveRegular(
            game=self, player=player, played_time=played_time, img=img, new_tiles=new_tiles, previous_move=prev_move
        )
        return self._insert_move(m)

    def add_exchange(self, player: int, played_time: tuple[int, int], img: MatLike) -> Game:
        """add exchange move"""
        prev_move = self.moves[-1] if self.moves else None
        m = MoveExchange(game=self, player=player, played_time=played_time, img=img, previous_move=prev_move)
        return self._insert_move(m)

    def add_two_exchanges_at(self, index: int) -> Game:
        """add exchange move at move index (index)"""
        if not self.valid_index(index=index):
            logger.error(f'invalid index {index}')
            # raise IndexError(f'add challenge at: invalid index {index}')
            return self
        player1, player2 = (self.moves[index].player, abs(self.moves[index].player - 1))
        played_time = self.moves[index - 1].played_time if index > 0 else (0, 0)
        img = self.moves[index].img.copy() if self.moves[index].img is not None else None  # type: ignore[attr-defined,union-attr]
        return self.insert_moves_at( index,
                    [ MoveExchange(game=self, player=player1, played_time=played_time, img=img, previous_move=None),
                      MoveExchange(game=self, player=player2, played_time=played_time, img=img, previous_move=None), ],
                )  # fmt: off

    def add_challenge_for(self, index: int = -1) -> Game:
        """add challenge malus for move at index (or at end)"""
        if not self.valid_index(index=index):
            logger.error(f'invalid index {index}')
            # raise IndexError(f'add challenge at: invalid index {index}')
            return self

        move_to_challenge = self.moves[index]
        if not isinstance(move_to_challenge, (MoveChallenge, MoveRegular, MoveUnknown)):
            logger.warning(f'challenge not allowed: {str(move_to_challenge)}')
            return self

        player = abs(move_to_challenge.player - 1)
        played_time = move_to_challenge.played_time
        m = MoveChallenge(game=self, player=player, played_time=played_time, previous_move=move_to_challenge)
        if index in (-1, len(self.moves) - 1):
            return self._insert_move(m)
        return self._insert_move(m, index=index + 1, recalc_from=index + 1)

    def add_withdraw_for(self, index: int, img: MatLike) -> Game:
        """add withdraw for move at index (or at end)"""
        if not self.valid_index(index=index):
            logger.error(f'invalid index {index}')
            # raise IndexError(f'add withdraw at: invalid index {index}')
            return self

        move_to_withdraw = self.moves[index]
        if not isinstance(move_to_withdraw, (MoveChallenge, MoveRegular, MoveUnknown)):
            logger.warning(f'withdraw not allowed: {str(move_to_withdraw)}')
            return self

        played_time = move_to_withdraw.played_time
        m = MoveWithdraw( game=self, player=move_to_withdraw.player, played_time=played_time,
                             img=img, previous_move=move_to_withdraw )  # fmt:off
        if index in (-1, len(self.moves) - 1):
            return self._insert_move(m)
        return self._insert_move(m, index=index + 1, recalc_from=index + 1)

    def toggle_challenge_type(self, index: int) -> Game:
        """toogle challenge"""
        to_change = self.moves[index]
        player = abs(to_change.player - 1)
        if isinstance(to_change, MoveChallenge):
            self.moves[index] = MoveWithdraw(game=self, player=player, played_time=to_change.played_time,
                                        img=to_change.img, previous_move=to_change.previous_move)  # fmt:off
        elif isinstance(to_change, MoveWithdraw):
            self.moves[index] = MoveChallenge(game=self, player=player, played_time=to_change.played_time, # type: ignore[assignment]
                                        previous_move=to_change.previous_move)  # fmt:off
        else:
            logger.debug(f'toggle_challenge_type not possible for move type {type(to_change).__name__} at index {index}')
            return self
        self._update_technical_move_attributes()
        self._recalculate_from(index)  # recalculate all moves from index
        self._write_json_from(index=index, write_mode=[JSON_FLAG])
        return self

    def add_unknown(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, player: int, played_time: tuple[int, int], img: MatLike, new_tiles: BoardType, removed_tiles: BoardType
    ) -> Game:
        """add unknown move"""
        prev_move = self.moves[-1] if self.moves else None
        m = MoveUnknown( game=self, player=player, played_time=played_time, img=img,
            new_tiles=new_tiles, removed_tiles=removed_tiles, previous_move=prev_move )  # fmt: off
        return self._insert_move(m)

    def add_lastrack(self) -> Game:
        """add lastrack malus/bonus (called by end of game)"""
        if not self.moves:
            logger.error('no previous move available, cannot calculate bonus/malus')
            # raise ValueError('add last rack: no previous move available')  # pylint: disable=broad-exception-raised
            return self
        prev_move = self.moves[-1]
        rack_str = ''.join(self.tiles_in_bag())
        if prev_move.rack_size[0] == 0:
            player1, player2 = 0, 1
        elif prev_move.rack_size[1] == 0:
            player1, player2 = 1, 0
        else:
            logger.warning(f'calculation impossible, no player has an empty rack. Rack size={prev_move.rack_size}')
            player1, player2, rack_str = 0, 1, '?'
        self._insert_move(MoveLastRackBonus(game=self, player=player1, previous_move=prev_move, rack=rack_str))
        self._insert_move(MoveLastRackMalus(game=self, player=player2, previous_move=self.moves[-1], rack=rack_str))
        return self

    def add_timeout_malus(self) -> Game:
        """add timeout malus (called by end of game)"""
        prev_move = self.moves[-1] if self.moves else None
        logger.debug('add timeout malus')
        move = MoveTimeMalus(game=self, player=0, previous_move=prev_move)
        if move.points != 0:
            self._insert_move(move)
            prev_move = self.moves[-1]
        move = MoveTimeMalus(game=self, player=1, previous_move=prev_move)
        if move.points != 0:
            self._insert_move(move)
        return self

    def replace_blank_with(self, coordinates: CoordType, char: str) -> Game:
        """replace blank at (coordinates) with (char)"""
        char = char.strip().lower()[0]  # use only first char transform to lower
        modified_indices = set()
        for i, m in enumerate(self.moves):
            updated = False
            if coordinates in m.board:
                m.board[coordinates] = Tile(char, MAX_TILE_PROB)
                updated = True
            if isinstance(m, MoveRegular) and coordinates in m.new_tiles:
                m.new_tiles[coordinates] = Tile(char, MAX_TILE_PROB)
                m.calculate_word()
                updated = True
            if updated:
                modified_indices.add(i)
        if modified_indices:
            self._write_json_from(index=min(modified_indices), write_mode=[JSON_FLAG])
        return self

    def remove_blank(self, coordinates: CoordType) -> Game:
        """remove blank at (coordinates)"""
        modified_indices = set()
        for i, m in enumerate(self.moves):
            updated = False
            if coordinates in m.board:
                m.board.pop(coordinates)
                updated = True
            if coordinates in m.new_tiles:
                m.new_tiles.pop(coordinates)
                m.is_modified = True
                updated = True
            if updated:
                modified_indices.add(i)
        if modified_indices:
            min_index = min(modified_indices)
            self._update_technical_move_attributes()
            self._recalculate_from(index=min_index)  # recalculate all moves from index
            self._write_json_from(index=min_index, write_mode=[JSON_FLAG])
        return self

    def remove_move_at(self, index: int) -> Game:
        """remove move before move at index (index) without checks"""
        if not self.valid_index(index=index):
            logger.error(f'invalid index {index}')
            # raise IndexError(f'remove move at: invalid index {index}')
            return self

        logger.info(f'remove move: {str(self.moves[index])}')
        self.moves.pop(index)
        self._update_technical_move_attributes()
        self._recalculate_from(index)  # recalculate all moves from index
        self._write_json_from(index=index, write_mode=[JSON_FLAG, IMAGE_FLAG])
        return self

    def change_move_at(self, index: int, movetype: MoveType, new_tiles: BoardType | None = None) -> Game:
        """change move before move at index (index)"""
        if not self.valid_index(index=index):
            logger.error(f'invalid index {index}')
            # raise IndexError(f'change move at: invalid index {index}')
            return self

        move_to_change = self.moves[index]
        if movetype == MoveType.REGULAR:
            if isinstance(move_to_change, MoveRegular):
                if new_tiles:
                    move_to_change.new_tiles = new_tiles.copy()
            elif new_tiles:
                self.moves[index] = MoveRegular(
                    game=self, player=move_to_change.player, played_time=move_to_change.played_time,
                    img=move_to_change.img, new_tiles=new_tiles, previous_move=move_to_change.previous_move,
                )  # fmt: off
        elif movetype == MoveType.EXCHANGE:
            self.moves[index] = MoveExchange(
                game=self, player=move_to_change.player, played_time=move_to_change.played_time,
                img=move_to_change.img, previous_move=move_to_change.previous_move,
            )  # fmt:off
        else:
            logger.warning(f'ignored due to invalid move type {movetype}')
            return self

        self._update_technical_move_attributes()
        self._recalculate_from(index)  # recalculate all moves from index
        self._write_json_from(index=index, write_mode=[JSON_FLAG, IMAGE_FLAG])
        return self

    def insert_moves_at(self, index: int | None, moves_to_insert: Sequence[Move]) -> Game:
        """insert move before position at (index)
        if index is None, the moves are appended to the end"""

        if not moves_to_insert:
            logger.warning(f'nothing to insert {moves_to_insert} size {len(moves_to_insert)}')
            return self
        if index is None:
            self.moves.extend(moves_to_insert)  # append to end
            index = -len(moves_to_insert)
        else:
            if not self.valid_index(index=index):
                logger.error(f'invalid index {index}')
                # raise IndexError(f'move to insert: invalid index {index}')
                return self
            self.moves[index:index] = moves_to_insert  # insert into slice
        self._update_technical_move_attributes()
        self._recalculate_from(index)
        self._write_json_from(index=index, write_mode=[JSON_FLAG, IMAGE_FLAG])
        return self
