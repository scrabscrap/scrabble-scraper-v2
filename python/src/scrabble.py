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
import re
from collections import Counter
from collections.abc import Generator, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

import cv2
from cv2.typing import MatLike

from config import config, version
from game_board.board import DOUBLE_LETTER, DOUBLE_WORDS, TRIPLE_LETTER, TRIPLE_WORDS
from game_board.tiles import bag_as_list, scores

API_VERSION = '1.3'
SCRABBLE_BONUS = 50
MAX_TILE_PROB = 99
ORD_A = ord('A')


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


def gcg_to_coord(gcg_string: str) -> tuple[bool, tuple[int, int]]:
    """convert gcg coordinates to board coordinates"""
    gcg_coord_h = re.compile('([A-Oa-o])(\\d+)')
    gcg_coord_v = re.compile('(\\d+)([A-Oa-o])')

    col, row = (0, 0)
    vert = False
    if gcg_match := gcg_coord_v.match(gcg_string):
        col = int(gcg_match.group(1)) - 1
        row = int(ord(gcg_match.group(2).capitalize()) - ORD_A)
        vert = True
    if gcg_match := gcg_coord_h.match(gcg_string):
        col = int(gcg_match.group(2)) - 1
        row = int(ord(gcg_match.group(1).capitalize()) - ORD_A)
        vert = False
    return vert, (col, row)


class MoveType(Enum):
    """Enumeration for move types"""

    REGULAR = auto()
    PASS_TURN = auto()
    EXCHANGE = auto()
    WITHDRAW = auto()
    CHALLENGE_BONUS = auto()
    LAST_RACK_BONUS = auto()
    LAST_RACK_MALUS = auto()
    TIME_MALUS = auto()
    UNKNOWN = auto()


class InvalidMoveError(Exception):
    """Exception for invalid moves"""

    pass


class NoMoveError(Exception):
    """Exception for no move"""

    pass


gcg_strings: dict = {
    MoveType.REGULAR: '> {m.mod_str}{m.player_name}: {m.gcg_coord} {m.gcg_word} {m.points} {m.player_score}',
    MoveType.PASS_TURN: '> {m.mod_str}{m.player_name}: -  {m.points} {m.player_score}',
    MoveType.EXCHANGE: '> {m.mod_str}{m.player_name}: -  {m.points} {m.player_score}',
    MoveType.WITHDRAW: '> {m.mod_str}{m.player_name}: -- {m.points} {m.player_score}',
    MoveType.CHALLENGE_BONUS: '> {m.mod_str}{m.player_name}: (challenge) {m.points} {m.player_score}',
    MoveType.LAST_RACK_BONUS: '> {m.mod_str}{m.player_name}: bank={m.rack} {m.points} {m.player_score}',
    MoveType.LAST_RACK_MALUS: '> {m.mod_str}{m.player_name}: bank={m.rack} {m.points} {m.player_score}',
    MoveType.TIME_MALUS: '> {m.mod_str}{m.player_name}: (time) {m.points} {m.player_score}',
    MoveType.UNKNOWN: '> {m.mod_str}{m.player_name}: (unknown) ? {m.player_score}',
}


dev_strings: dict = {
    MoveType.REGULAR: '{m.move}, "{button}", "{status}", "{m.gcg_coord}", "{m.word}", {m.points}, {m.score[0]}, {m.score[1]}',
    MoveType.PASS_TURN: '{m.move}, "{button}", "{status}", "-", "", {m.points}, {m.score[0]}, {m.score[1]}',
    MoveType.EXCHANGE: '{m.move}, "{button}", "{status}", "-", "", {m.points}, {m.score[0]}, {m.score[1]}',
    MoveType.WITHDRAW: '{m1.move}, "YELLOW", "{status1}", "{m1.gcg_coord}", "{m1.word}", {m1.points}, '
    '{m1.score[0]}, {m1.score[1]}\n'
    '{m2.move}, "{button}", "{status1}", "--", "{m2.word}", {m2.points}, {m2.score[0]}, {m2.score[1]}\n'
    '{m2.move}, "YELLOW", "{status2}", "--", "{m2.word}", {m2.points}, {m2.score[0]}, {m2.score[1]}',
    MoveType.CHALLENGE_BONUS: '{m1.move}, "YELLOW", "{status1}", "{m1.gcg_coord}", "{m1.word}", {m1.points}, '
    '{m1.score[0]}, {m1.score[1]}\n'
    '{m2.move}, "{button}", "{status1}", "--", "", {m2.points}, {m2.score[0]}, {m2.score[1]}\n'
    '{m2.move}, "YELLOW", "{status2}", "--", "", {m2.points}, {m2.score[0]}, {m2.score[1]}',
    MoveType.LAST_RACK_BONUS: '{m.move}, "EOG", "(rack)", "", "{m.rack}", {m.points}, {m.score[0]}, {m.score[1]}',
    MoveType.LAST_RACK_MALUS: '{m.move}, "EOG", "(rack)", "", "{m.rack}", {m.points}, {m.score[0]}, {m.score[1]}',
    MoveType.TIME_MALUS: '{m.move}, "", "(time)", "", "", {m.points}, {m.score[0]}, {m.score[1]}',
    MoveType.UNKNOWN: '{m.move}, "", "(unknown)", "", "", , {m.score[0]}, {m.score[1]}',
}


@dataclass
class Tile:
    """one tile on Board"""

    letter: str  # letter
    prob: int  # probability of recognition


# type BoardType = dict[tuple[int, int], Tile]  # python > 3.12
# type CoordType = tuple[int, int] # python > 3.12
CoordType = tuple[int, int]
BoardType = dict[CoordType, Tile]


@dataclass(kw_only=True)
class Move:  # pylint: disable=too-many-instance-attributes
    """Represents a Move"""

    type: MoveType
    game: Game
    time: str = str(datetime.now())

    move: int = field(default=0)
    player: int
    played_time: tuple[int, int] = (0, 0)
    img: MatLike | None = field(repr=False)
    new_tiles: BoardType = field(default_factory=dict)

    points: int = 0
    score: tuple[int, int] = (0, 0)
    is_modified: bool = False

    board: BoardType = field(default_factory=dict)
    rack_size: tuple[int, int] = (7, 7)
    previous_move: Move | None = None

    def __post_init__(self) -> None:
        self.new_tiles = {}
        self.setup_board()
        self.calculate_score()

    def __str__(self) -> str:
        """move as json string"""
        return self.gcg_str

    def setup_board(self) -> BoardType:
        """initialize board"""
        try:
            previous_board = self.previous_move.board if self.previous_move else {}
            self.board = {**previous_board}
        except AttributeError:
            logging.warning('Previous board not available. Initializing empty board.')
            self.board = {}
        return self.board

    def calculate_points(self) -> tuple[int, bool]:
        """calculates and sets points and returns whether the move is a Scrabble"""
        self.points = 0
        return self.points, False

    def calculate_rack_size(self) -> tuple[int, int]:
        """calculates and sets racksize after this move"""
        self.rack_size = self.previous_move.rack_size if self.previous_move else (7, 7)
        return self.rack_size

    def calculate_score(self) -> tuple[int, tuple[int, int]]:
        """calculates and sets score after move"""
        previous_score = self.previous_move.score if self.previous_move else (0, 0)
        self.calculate_rack_size()
        self.calculate_points()
        dx, dy = ((self.points, 0), (0, self.points))[self.player]
        self.score = (previous_score[0] + dx, previous_score[1] + dy)
        logging.debug(f'{str(self)} -> {self.score}')
        return self.points, self.score

    def calculate_word(self) -> str:
        """returns word of move"""
        return ''

    @property
    def gcg_str(self) -> str:
        """move as gcg string"""
        return gcg_strings[self.type].format(m=self)

    @property
    def dev_str(self) -> str:
        """returns a string for GCG"""
        return dev_strings[self.type].format(m=self, button=('Green', 'Red')[self.player], status=('S1', 'S0')[self.player])

    @property
    def mod_str(self) -> str:
        """modification string for gcg"""
        return f' {chr(0x270F)}' if self.is_modified else ''  # ✏

    @property
    def player_name(self) -> str:
        """name of current player"""
        return self.game.nicknames[self.player]

    @property
    def player_score(self) -> int:
        """score of current player"""
        return self.score[self.player]

    @property
    def player_time(self) -> int:
        """returns played time of current player"""
        return self.played_time[self.player]

    @property
    def gcg_coord(self) -> str:
        """returns coordinate in GCG format"""
        return '   '

    def calc_coord(self, coord: str) -> tuple[bool, CoordType]:
        """calc coord from gcg string"""
        return gcg_to_coord(coord)


@dataclass(kw_only=True)
class MoveRegular(Move):  # pylint: disable=too-many-instance-attributes
    """regular move"""

    type: MoveType = MoveType.REGULAR
    coord: tuple[int, int] = field(init=False)
    is_vertical: bool = field(init=False)
    new_tiles: BoardType = field(default_factory=dict, init=True)
    is_scrabble: bool = field(default=False)
    word: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.new_tiles:
            raise NoMoveError
        self.setup_board()
        self.calculate_coord()
        self.calculate_score()

    @property
    def gcg_coord(self) -> str:
        """convert board coordinates to gcg coordinates"""
        (col, row) = self.coord
        return f'{col + 1}{chr(row + ORD_A)}' if self.is_vertical else f'{chr(row + ORD_A)}{col + 1}'

    @property
    def gcg_word(self) -> str:
        """builds a gcg word"""
        (col, row) = self.coord
        gcg_str = []
        for pos, char in enumerate(self.word):
            if char == '.':
                cell = self.board[(col, row + pos)] if self.is_vertical else self.board[(col + pos, row)]
                gcg_str.append(f'({cell.letter})')
            else:
                gcg_str.append(char)
        return ''.join(gcg_str).replace(')(', '')

    def setup_board(self) -> BoardType:
        super().setup_board()
        self.board.update(self.new_tiles)
        return self.board

    def calculate_rack_size(self) -> tuple[int, int]:
        (rack0, rack1) = self.previous_move.rack_size if self.previous_move else (7, 7)
        tiles_on_board: int = len(self.previous_move.board) if self.previous_move else 0
        take_tiles = len(self.new_tiles)
        in_bag = len(bag_as_list) - tiles_on_board - rack0 - rack1
        if self.player == 0:
            remain = rack0 - take_tiles + min(take_tiles, in_bag)
            self.rack_size = (remain, rack1)
        else:
            remain = rack1 - take_tiles + min(take_tiles, in_bag)
            self.rack_size = (rack0, remain)
        return self.rack_size

    def _find_start(self, coord: CoordType, vertical: bool) -> CoordType:
        """find word start coordinates"""
        col, row = coord
        d_col, d_row = (0, -1) if vertical else (-1, 0)  # find start
        while (col + d_col, row + d_row) in self.board:
            col, row = (col + d_col, row + d_row)
        return (col, row)

    def calculate_points(self) -> tuple[int, bool]:
        def get_letter_bonus(coord: CoordType) -> int:
            return 2 if coord in DOUBLE_LETTER else 3 if coord in TRIPLE_LETTER else 1

        def get_word_multiplier(coord: CoordType) -> int:
            return 2 if coord in DOUBLE_WORDS else 3 if coord in TRIPLE_WORDS else 1

        def collect_word_coords(coord: CoordType, vertical: bool) -> Generator[CoordType]:
            col, row = coord
            d_col, d_row = (0, 1) if vertical else (1, 0)  # collect word
            while (col, row) in self.board:
                yield (col, row)
                col, row = (col + d_col, row + d_row)

        def crossing_word_score(coord: CoordType, vertical: bool) -> int:
            start = self._find_start(coord, vertical)
            coords = list(collect_word_coords(start, vertical))
            if len(coords) <= 1:
                return 0
            score = 0
            word_multiplier = 1
            for pos in coords:  # vertical to new word
                if pos in self.new_tiles:
                    score += scores(self.board[pos].letter) * get_letter_bonus(pos)
                    word_multiplier *= get_word_multiplier(pos)
                else:
                    score += scores(self.board[pos].letter)
            return score * word_multiplier

        if self.type is not MoveType.REGULAR:
            return 0, False

        points = 0
        crossing_words_score = 0
        word_multiplier = 1
        for coord in collect_word_coords(self._find_start(self.coord, self.is_vertical), self.is_vertical):
            if coord in self.new_tiles:
                points += scores(self.board[coord].letter) * get_letter_bonus(coord=coord)
                word_multiplier *= get_word_multiplier(coord=coord)
                crossing_words_score += crossing_word_score(coord=coord, vertical=not self.is_vertical)
            else:
                points += scores(self.board[coord].letter)

        self.points = points * word_multiplier + crossing_words_score
        self.is_scrabble = len(self.new_tiles) >= 7
        if self.is_scrabble:
            self.points += SCRABBLE_BONUS
        return self.points, self.is_scrabble

    def calculate_coord(self) -> tuple[bool, CoordType]:
        """find begin and orientation of new word"""
        # Determine direction
        if not self.new_tiles:
            return False, (-1, -1)
        changed = sorted(self.new_tiles)  # ensure sorted
        horizontal = len(Counter(col for col, _ in changed)) > 1
        self.is_vertical = len(Counter(row for _, row in changed)) > 1
        if self.is_vertical and horizontal:
            raise ValueError(f'move: illegal move horizontal and vertical changes detected {changed}')
        if len(self.new_tiles) == 1:  # only 1 tile
            (col, row) = list(self.new_tiles.keys())[0]
            horizontal = (col - 1, row) in self.board or (col + 1, row) in self.board
            self.is_vertical = not horizontal
        self.coord = self._find_start(changed[0], self.is_vertical)
        self.calculate_word()
        return self.is_vertical, self.coord

    def calculate_word(self) -> str:
        """returns word of move"""
        new_tiles = {**self.new_tiles}
        d_col, d_row = (0, 1) if self.is_vertical else (1, 0)
        col, row = self.coord
        self.word = ''
        while (col, row) in self.board:
            self.word += self.board[(col, row)].letter if (col, row) in self.new_tiles else '.'
            if (col, row) in self.new_tiles:
                new_tiles.pop((col, row))
            (col, row) = (col + d_col, row + d_row)
        if new_tiles:
            raise ValueError(f'can not build word (tiles remaining {new_tiles})')
        return self.word


@dataclass(kw_only=True)
class MoveExchange(Move):
    """exchange move"""

    type: MoveType = MoveType.EXCHANGE


@dataclass(kw_only=True)
class MoveWithdraw(Move):
    """withdraw move"""

    type: MoveType = MoveType.WITHDRAW
    removed_tiles: BoardType = field(init=False)
    word: str = field(init=False)

    def __post_init__(self) -> None:
        if self.previous_move and isinstance(self.previous_move, MoveRegular):
            self.removed_tiles = self.previous_move.new_tiles.copy()
            self.word = self.previous_move.word
        else:
            self.removed_tiles = {}
            self.word = ''
        super().__post_init__()

    def setup_board(self) -> BoardType:
        super().setup_board()
        for key in self.removed_tiles.keys():
            if key in self.board:
                deleted = self.board.pop(key, None)
                logging.debug(f'removed tile: {deleted}')
        return self.board

    def calculate_rack_size(self) -> tuple[int, int]:
        move_to_withdraw = self.previous_move if self.previous_move else None
        move_to_restore = move_to_withdraw.previous_move if move_to_withdraw else None
        self.rack_size = move_to_restore.rack_size if move_to_restore else (7, 7)
        return self.rack_size

    def calculate_points(self) -> tuple[int, bool]:
        self.points = -self.previous_move.points if self.previous_move else 0
        return self.points, False

    @property
    def dev_str(self) -> str:
        return dev_strings[self.type].format(
            m1=self.previous_move,
            status1=('P0', 'P1')[self.player],
            button=('DOUBT1', 'DOUBT0')[self.player],
            m2=self,
            status2=('S0', 'S1')[self.player],
        )


@dataclass(kw_only=True)
class MoveChallenge(Move):
    """incorrect challenge move"""

    type: MoveType = MoveType.CHALLENGE_BONUS
    img: MatLike | None = field(repr=False, init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.previous_move:
            self.img = self.previous_move.img.copy() if self.previous_move.img is not None else None

    def calculate_points(self) -> tuple[int, bool]:
        self.points = -config.scrabble.malus_doubt
        return self.points, False

    @property
    def dev_str(self) -> str:
        return dev_strings[self.type].format(
            m1=self.previous_move,
            status1=('P0', 'P1')[self.player],
            button=('DOUBT0', 'DOUBT1')[self.player],
            m2=self,
            status2=('S0', 'S1')[self.player],
        )


@dataclass(kw_only=True)
class MoveLastRackBonus(Move):
    """last rack bonus"""

    type: MoveType = MoveType.LAST_RACK_BONUS
    rack: str = field(default='')
    img: MatLike | None = field(repr=False, init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.previous_move:
            self.img = self.previous_move.img.copy() if self.previous_move.img is not None else None
            self.played_time = self.previous_move.played_time

    def calculate_points(self) -> tuple[int, bool]:
        self.points = 0 if self.rack == '?' else sum(scores(c) for c in self.rack)
        return self.points, False


@dataclass(kw_only=True)
class MoveLastRackMalus(Move):
    """last rack malus"""

    type: MoveType = MoveType.LAST_RACK_MALUS
    rack: str = field(default='')
    img: MatLike | None = field(repr=False, init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.previous_move:
            self.img = self.previous_move.img.copy() if self.previous_move.img is not None else None
            self.played_time = self.previous_move.played_time

    def calculate_points(self) -> tuple[int, bool]:
        self.points = 0 if self.rack == '?' else -sum(scores(c) for c in self.rack)
        return self.points, False


@dataclass(kw_only=True)
class MoveTimeMalus(Move):
    """timeout malus"""

    type: MoveType = MoveType.TIME_MALUS
    img: MatLike | None = field(repr=False, init=False)

    def __post_init__(self) -> None:
        if self.previous_move:
            self.img = self.previous_move.img.copy() if self.previous_move.img is not None else None
            self.played_time = self.previous_move.played_time
        super().__post_init__()

    def calculate_points(self) -> tuple[int, bool]:
        self.points = 0
        if config.scrabble.max_time - self.player_time < 0:
            self.points = ((config.scrabble.max_time - self.player_time) // 60) * config.scrabble.timeout_malus
        return self.points, False


@dataclass(kw_only=True)
class MoveUnknown(Move):
    """unknown move (incorrect move)"""

    type: MoveType = MoveType.UNKNOWN
    new_tiles: BoardType = field(default_factory=dict, init=True)
    removed_tiles: BoardType = field(default_factory=dict, init=True)


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
            keys1 = [chr(ord('a') + y) + str(x + 1) for (x, y) in move.board.keys()]
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

        bag = bag_as_list.copy()
        for i in values:
            if i in bag:
                bag.remove(i)
        return bag

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

    def _write_json_from(self, index: int, write_mode: list[str]) -> Game:
        """write json for move"""
        if config.is_testing:  # skip if under test
            return self
        if index < 0:
            index += len(self.moves)
        if index >= len(self.moves):
            logging.warning(f'invalid index {index} skipped')
            return self

        for i in range(index, len(self.moves)):  # write json and images
            if 'json' in write_mode:
                with open(f'{config.path.web_dir}/data-{i}.json', 'w', encoding='utf-8') as json_file:
                    json.dump(self._get_json_data(index=i), json_file, indent=4)
            if 'image' in write_mode and self.moves[index].img is not None:
                cv2.imwrite(f'{config.path.web_dir}/image-{i}.jpg', self.moves[index].img, [cv2.IMWRITE_JPEG_QUALITY, 100])  # type:ignore
            if i == len(self.moves) - 1:
                with open(f'{config.path.web_dir}/status.json', 'w', encoding='utf-8') as json_file:
                    json.dump(self._get_json_data(index=i), json_file, indent=4)
        # logging.debug(f'{self.json_str(index=index)[: self.json_str(index=index).find("moves") + 7]} ...')
        return self

    def _add_move(self, move: Move, index: int = -1, recalc_from: int | None = None) -> Game:
        if index == -1:
            self.moves.append(move)
        else:
            self.moves.insert(index, move)
        self._update_technical_move_attributes()
        if recalc_from is not None:
            self._recalculate_from(recalc_from)
        logging.info(f'add move: {str(move)}')
        self._write_json_from(index=(index if index != -1 else len(self.moves) - 1), write_mode=['json', 'image'])
        return self

    def add_regular(self, player: int, played_time: tuple[int, int], img: MatLike, new_tiles: BoardType) -> Game:
        """add regular move"""
        prev_move = self.moves[-1] if self.moves else None
        m = MoveRegular(
            game=self, player=player, played_time=played_time, img=img, new_tiles=new_tiles, previous_move=prev_move
        )
        return self._add_move(m)

    def add_exchange(self, player: int, played_time: tuple[int, int], img: MatLike) -> Game:
        """add exchange move"""
        prev_move = self.moves[-1] if self.moves else None
        m = MoveExchange(game=self, player=player, played_time=played_time, img=img, previous_move=prev_move)
        return self._add_move(m)

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
            logging.warning(f'(challenge not allowed: {str(move_to_challenge)}')
            return self

        player = abs(move_to_challenge.player - 1)
        played_time = move_to_challenge.played_time
        m = MoveChallenge(game=self, player=player, played_time=played_time, previous_move=move_to_challenge)
        if index in (-1, len(self.moves) - 1):
            return self._add_move(m)
        return self._add_move(m, index=index + 1, recalc_from=index + 1)

    def add_withdraw_for(self, index: int, img: MatLike) -> Game:
        """add withdraw for move at index (or at end)"""
        if not self.valid_index(index=index):
            raise IndexError(f'add withdraw at: invalid index {index}')

        move_to_withdraw = self.moves[index]
        if not isinstance(move_to_withdraw, (MoveChallenge, MoveRegular, MoveUnknown)):
            logging.warning(f'(withdraw not allowed: {str(move_to_withdraw)}')
            return self

        played_time = move_to_withdraw.played_time
        m = MoveWithdraw( game=self, player=move_to_withdraw.player, played_time=played_time,
                             img=img, previous_move=move_to_withdraw )  # fmt:off
        if index in (-1, len(self.moves) - 1):
            return self._add_move(m)
        return self._add_move(m, index=index + 1, recalc_from=index + 1)

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
            logging.debug('not expected: invalid move type for toggle challenge')
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
        return self._add_move(m)

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
            logging.warning(f'last rack calculation impossible: rack size={prev_move.rack_size}')
            player1, player2, rack_str = 0, 1, '?'
        self._add_move(MoveLastRackBonus(game=self, player=player1, previous_move=prev_move, rack=rack_str))
        self._add_move(MoveLastRackMalus(game=self, player=player2, previous_move=self.moves[-1], rack=rack_str))
        return self

    def add_timeout_malus(self) -> Game:
        """add timeout malus (called by end of game)"""
        prev_move = self.moves[-1] if self.moves else None
        logging.debug('scrabble: create move timeout malus')
        move = MoveTimeMalus(game=self, player=0, previous_move=prev_move)
        if move.points != 0:
            self._add_move(move)
            prev_move = self.moves[-1]
        move = MoveTimeMalus(game=self, player=1, previous_move=prev_move)
        if move.points != 0:
            self._add_move(move)
        return self

    def replace_blank_with(self, coordinates: CoordType, char: str) -> Game:
        """replace blank at (coordinates) with (char)"""
        char = char.strip().lower()[0]  # use only first char transform to lower
        modified = None
        for i, m in enumerate(self.moves):
            if coordinates in m.board:
                m.board[coordinates] = Tile(char, MAX_TILE_PROB)
                modified = modified if modified else i
            if isinstance(m, MoveRegular) and coordinates in m.new_tiles:
                m.new_tiles[coordinates] = Tile(char, MAX_TILE_PROB)
                modified = modified if modified else i
                m.calculate_word()  # update word text
        if modified:
            self._write_json_from(index=modified, write_mode=['json'])
        return self

    def remove_blank(self, coordinates: CoordType) -> Game:
        """remove blank at (coordinates)"""
        modified_index = None
        for i, m in enumerate(self.moves):
            if coordinates in m.board:
                m.board.pop(coordinates)
                modified_index = modified_index if modified_index else i
            if coordinates in m.new_tiles:
                m.new_tiles.pop(coordinates)
                m.is_modified = True
                modified_index = modified_index if modified_index else i
        if modified_index:
            self._update_technical_move_attributes()
            self._recalculate_from(index=modified_index)  # recalculate all moves from index
            self._write_json_from(index=modified_index, write_mode=['json'])
        return self

    def remove_move_at(self, index: int) -> Game:
        """remove move abeforet move at index (index) without checks"""
        if not self.valid_index(index=index):
            raise IndexError(f'remove move at: invalid index {index}')

        logging.info(f'remove move: {str(self.moves[index])}')
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
        match movetype:
            case MoveType.REGULAR:
                if isinstance(move_to_change, MoveRegular):
                    if new_tiles:
                        move_to_change.new_tiles = new_tiles.copy()
                else:
                    if new_tiles:
                        m = MoveRegular(
                            game=self,
                            player=move_to_change.player,
                            played_time=move_to_change.played_time,
                            img=move_to_change.img,
                            new_tiles=new_tiles,
                            previous_move=move_to_change.previous_move,
                        )
                        self.moves[index] = m
            case MoveType.EXCHANGE:
                exchange = MoveExchange(
                    game=self,
                    player=move_to_change.player,
                    played_time=move_to_change.played_time,
                    img=move_to_change.img,
                    previous_move=move_to_change.previous_move,
                )
                self.moves[index] = exchange
            case _:
                logging.warning(f'ignore change at: invalid move type {movetype}')

        self._update_technical_move_attributes()
        self._recalculate_from(index)  # recalculate all moves from index
        self._write_json_from(index=index, write_mode=['json', 'image'])
        return self

    def insert_moves_at(self, index: int | None, moves_to_insert: Sequence[Move]) -> Game:
        """insert move before position at (index)
        if index is None, the moves are appended to the end"""

        if not moves_to_insert:
            logging.warning(f'nothing to insert {moves_to_insert} size {len(moves_to_insert)}')
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
