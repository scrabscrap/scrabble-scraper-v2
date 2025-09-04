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
import re
from collections import Counter
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING

from cv2.typing import MatLike

from config import BAGS, DOUBLE_LETTER, DOUBLE_WORDS, SCORES, TRIPLE_LETTER, TRIPLE_WORDS, config

if TYPE_CHECKING:
    from scrabble import Game

SCRABBLE_BONUS = 50
MAX_TILE_PROB = 99
ORD_A = ord('A')

logger = logging.getLogger()
bag = BAGS[config.board.language]
bag_as_list = [k for k, count in bag.items() for _ in range(count)]


def scores(tile: str) -> int:
    """returns 0 if  '_' or lower chars otherwise the scoring value"""
    return 0 if tile.islower() or tile == '_' else SCORES[config.board.language][tile]


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


class NoMoveError(Exception):
    """Exception for no move"""


gcg_strings: dict[MoveType, str] = {
    MoveType.REGULAR: '> {m.mod_str}{m.player_name}: {m.gcg_coord} {m.gcg_word} {m.points} {m.player_score}',
    MoveType.PASS_TURN: '> {m.mod_str}{m.player_name}: -  {m.points} {m.player_score}',
    MoveType.EXCHANGE: '> {m.mod_str}{m.player_name}: -  {m.points} {m.player_score}',
    MoveType.WITHDRAW: '> {m.mod_str}{m.player_name}: -- {m.points} {m.player_score}',
    MoveType.CHALLENGE_BONUS: '> {m.mod_str}{m.player_name}: (challenge) {m.points} {m.player_score}',
    MoveType.LAST_RACK_BONUS: '> {m.mod_str}{m.player_name}: rack={m.rack} {m.points} {m.player_score}',
    MoveType.LAST_RACK_MALUS: '> {m.mod_str}{m.player_name}: rack={m.rack} {m.points} {m.player_score}',
    MoveType.TIME_MALUS: '> {m.mod_str}{m.player_name}: (time) {m.points} {m.player_score}',
    MoveType.UNKNOWN: '> {m.mod_str}{m.player_name}: (unknown) ? {m.player_score}',
}


dev_strings: dict[MoveType, str] = {
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
    time: str = field(init=False)

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
        self.time = str(datetime.now())
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
            logger.warning('Previous board not available. Initializing empty board.')
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
        logger.debug(f'{str(self)} -> {self.score}')
        return self.points, self.score

    def calculate_word(self) -> str:
        """returns word of move"""
        return ''

    def cleanup_invalid_blanks(self, tiles_candidates: set) -> None:
        """cleanup invalid blanks"""
        if self.new_tiles:
            blanks_to_remove = [i for i in self.new_tiles if (self.board[i].letter == '_') and i not in tiles_candidates]
            for to_del in blanks_to_remove:
                del self.new_tiles[to_del]
            if blanks_to_remove:
                self.calculate_score()  # catch exception NoMoveException, InvalidMoveException

    @property
    def gcg_str(self) -> str:
        """move as gcg string"""
        return gcg_strings[self.type].format(m=self)

    @property
    def gcg_word(self) -> str:
        """move as gcg string"""
        return ''

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
        self.time = str(datetime.now())
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

    def _find_start(self, vertical: bool, coord: CoordType) -> CoordType:
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
            start = self._find_start(vertical, coord)
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
        for coord in collect_word_coords(self._find_start(self.is_vertical, self.coord), self.is_vertical):
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
            raise InvalidMoveError(f'move: illegal move horizontal and vertical changes detected {changed}')
        if len(self.new_tiles) == 1:  # only 1 tile
            (col, row) = list(self.new_tiles.keys())[0]
            horizontal = (col - 1, row) in self.board or (col + 1, row) in self.board
            self.is_vertical = not horizontal
        self.coord = self._find_start(self.is_vertical, changed[0])
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
            logger.error(f'can not build word (tiles remaining {new_tiles})')
            # raise ValueError(f'can not build word (tiles remaining {new_tiles})')
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
        for key in self.removed_tiles:
            if key in self.board:
                deleted = self.board.pop(key, None)
                logger.debug(f'removed tile: {deleted}')
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
    def gcg_word(self) -> str:
        return self.word

    @property
    def dev_str(self) -> str:
        return dev_strings[self.type].format(
            m1=self.previous_move,
            status1=('P1', 'P0')[self.player],
            button=('DOUBT1', 'DOUBT0')[self.player],
            m2=self,
            status2=('S1', 'S0')[self.player],
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

    @property
    def gcg_word(self) -> str:
        return self.rack


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

    @property
    def gcg_word(self) -> str:
        return self.rack


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

    def __post_init__(self) -> None:
        """initialize board"""
        self.time = str(datetime.now())
        previous_board = self.previous_move.board if self.previous_move else {}
        self.score = self.previous_move.score if self.previous_move else (0, 0)
        self.board = {**previous_board}
        self.board.update(self.new_tiles)
