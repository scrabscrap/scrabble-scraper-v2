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
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

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
from threadpool import Command
from upload import upload

API_VERSION = '1.3'
logger = logging.getLogger(__name__)


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

    def _get_json_data(self, index: int = -1) -> dict:
        """Return the json represention of the board"""

        name1, name2 = self.nicknames
        base_json = {
            'api': API_VERSION,
            'commit': version.git_commit,
            'layout': config.board.layout,
            'tournament': config.scrabble.tournament,
            'name1': name1,
            'name2': name2,
        }
        if not self.moves:
            data = base_json | {
                'time': str(self.gamestart),
                'move': 0, 'score1': 0, 'score2': 0,
                'time1': config.scrabble.max_time, 'time2': config.scrabble.max_time,
                'onmove': name1, 'moves': [], 'board': {}, 'props': {},
                'bag': bag_as_list.copy(),
            }  # fmt: off
        else:
            move_index = len(self.moves) + index if index < 0 else index
            move = self.moves[move_index]
            keys1 = [chr(ord('a') + y) + str(x + 1) for (x, y) in move.board]
            values1 = [tile.letter for tile in move.board.values()]
            prop1 = [tile.prob for tile in move.board.values()]
            gcg_moves = [self.moves[i].gcg_str for i in range(move_index + 1)]
            data = base_json | {
                'time': move.time, 'move': move.move,
                'score1': move.score[0], 'score2': move.score[1],
                'time1': config.scrabble.max_time - move.played_time[0],
                'time2': config.scrabble.max_time - move.played_time[1],
                'onmove': self.nicknames[move.player],
                'moves': gcg_moves,
                'board': dict(zip(keys1, values1)),
                'props': dict(zip(keys1, prop1)),
                'bag': self.tiles_in_bag(index),
            }  # fmt: off
        return data

    def json_str(self, index: int = -1) -> str:
        """Return the json represention of the board"""
        return json.dumps(self._get_json_data(index=index), indent=4)  # Add indent here

    def valid_index(self, index: int) -> bool:
        """is (index) valid"""
        return bool(self.moves) and -len(self.moves) <= index < len(self.moves)

    def dev_str(self) -> str:  # pragma: no cover
        """Return devleompemt represention of the game for using in tests"""
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
        self.nicknames = (name1, name2)
        self._write_json_from(index=-1, write_mode=[])  # only status file

    def new_game(self) -> Game:
        """Reset to a new game (nicknames, moves)"""
        self.nicknames = ('Name1', 'Name2')
        self.gamestart = datetime.now()
        self.moves.clear()
        self._write_json_from(index=-1, write_mode=[])  # only status file
        return self

    def end_game(self) -> Game:
        """finish game"""
        self.add_timeout_malus()
        self.add_lastrack()
        return self

    def tiles_in_bag(self, index: int = -1) -> list[str]:
        """returns list of tiles in bag"""
        tiles_on_board = self.moves[index].board.values() if self.moves else []
        values = ['_' if tile.letter.isalpha() and tile.letter.islower() else tile.letter for tile in tiles_on_board]

        b = bag_as_list.copy()
        for i in values:
            if i in b:
                b.remove(i)
        return b

    def get_coords_to_ignore(self) -> set[tuple[int, int]]:
        """Returns the coordinates that are to be ignored in the analysis."""
        if not self.moves:
            return set()
        to_verify = min(len(self.moves), config.scrabble.verify_moves)
        return set(self.moves[-to_verify].board.keys())

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

    def _write_json(self, i: int, web_dir: Path):
        json_path = web_dir / f'data-{i}.json'
        with json_path.open('w', encoding='utf-8') as json_file:
            json.dump(self._get_json_data(index=i), json_file, indent=4)

    def _write_image(self, i: int, web_dir: Path):
        img = self.moves[i].img
        if img is not None:
            image_path = web_dir / f'image-{i}.jpg'
            cv2.imwrite(str(image_path), img, [cv2.IMWRITE_JPEG_QUALITY, 100])  # type:ignore

    def _write_status(self, i: int, web_dir: Path):
        status_path = web_dir / 'status.json'
        with status_path.open('w', encoding='utf-8') as json_file:
            json.dump(self._get_json_data(index=i), json_file, indent=4)

    def _write_json_from(self, index: int, write_mode: list[str]) -> Game:
        """write json for move"""
        if config.is_testing:  # skip if under test
            return self
        index = index % len(self.moves)  # convert to positive index
        if not self.valid_index(index):
            logger.warning(f'invalid index {index} skipped')
            return self
        web_dir = Path(config.path.web_dir)
        write_json = 'json' in write_mode
        write_img = 'image' in write_mode

        for i in range(index, len(self.moves)):
            if write_json:
                self._write_json(i, web_dir)
            if write_img:
                self._write_image(i, web_dir)
            if i == len(self.moves) - 1:
                self._write_status(i, web_dir)
            if config.output.upload_server:
                upload.get_upload_queue().put_nowait(Command(upload.upload_move, index))
        return self

    def _insert_move(self, move: Move, index: int = -1, recalc_from: int | None = None) -> Game:
        if index == -1:
            self.moves.append(move)
        else:
            self.moves.insert(index, move)
        self._update_technical_move_attributes()
        if recalc_from is not None:
            self._recalculate_from(recalc_from)
        logger.info(f'add move: {str(move)}')
        self._write_json_from(index=(index if index != -1 else len(self.moves) - 1), write_mode=['json', 'image'])
        return self

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
        logger.info(f'new scores {self.moves[-1].score}:\n{self.board_str()}')
        if logger.isEnabledFor(logging.DEBUG):
            msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in self.moves)
            json_str = self.json_str()
            logger.debug(f'{msg}\napi: {json_str[: json_str.find("moves") + 7]}...\n')

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
            raise IndexError(f'add challenge at: invalid index {index}')
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
            raise IndexError(f'add challenge at: invalid index {index}')

        move_to_challenge = self.moves[index]
        if not isinstance(move_to_challenge, (MoveChallenge, MoveRegular, MoveUnknown)):
            logger.warning(f'(challenge not allowed: {str(move_to_challenge)}')
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
            raise IndexError(f'add withdraw at: invalid index {index}')

        move_to_withdraw = self.moves[index]
        if not isinstance(move_to_withdraw, (MoveChallenge, MoveRegular, MoveUnknown)):
            logger.warning(f'(withdraw not allowed: {str(move_to_withdraw)}')
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
            logger.debug('not expected: invalid move type for toggle challenge')
            return self
        self._update_technical_move_attributes()
        self._recalculate_from(index)  # recalculate all moves from index
        self._write_json_from(index=index, write_mode=['json'])
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
            raise ValueError('add last rack: no previous move available')  # pylint: disable=broad-exception-raised
        prev_move = self.moves[-1]
        rack_str = ''.join(self.tiles_in_bag())
        if prev_move.rack_size[0] == 0:
            player1, player2 = 0, 1
        elif prev_move.rack_size[1] == 0:
            player1, player2 = 1, 0
        else:
            logger.warning(f'last rack calculation impossible: rack size={prev_move.rack_size}')
            player1, player2, rack_str = 0, 1, '?'
        self._insert_move(MoveLastRackBonus(game=self, player=player1, previous_move=prev_move, rack=rack_str))
        self._insert_move(MoveLastRackMalus(game=self, player=player2, previous_move=self.moves[-1], rack=rack_str))
        return self

    def add_timeout_malus(self) -> Game:
        """add timeout malus (called by end of game)"""
        prev_move = self.moves[-1] if self.moves else None
        logger.debug('scrabble: create move timeout malus')
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
            self._write_json_from(index=min(modified_indices), write_mode=['json'])
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
            self._write_json_from(index=min_index, write_mode=['json'])
        return self

    def remove_move_at(self, index: int) -> Game:
        """remove move abeforet move at index (index) without checks"""
        if not self.valid_index(index=index):
            raise IndexError(f'remove move at: invalid index {index}')

        logger.info(f'remove move: {str(self.moves[index])}')
        self.moves.pop(index)
        self._update_technical_move_attributes()
        self._recalculate_from(index)  # recalculate all moves from index
        self._write_json_from(index=index, write_mode=['json', 'image'])
        return self

    def change_move_at(self, index: int, movetype: MoveType, new_tiles: BoardType | None = None) -> Game:
        """change move before move at index (index)"""
        if not self.valid_index(index=index):
            raise IndexError(f'change move at: invalid index {index}')

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
            logger.warning(f'ignore change at: invalid move type {movetype}')
            return self

        self._update_technical_move_attributes()
        self._recalculate_from(index)  # recalculate all moves from index
        self._write_json_from(index=index, write_mode=['json', 'image'])
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
                raise IndexError(f'move to insert: invalid index {index}')
            self.moves[index:index] = moves_to_insert  # insert into slice
        self._update_technical_move_attributes()
        self._recalculate_from(index)
        self._write_json_from(index=index, write_mode=['json', 'image'])
        return self
