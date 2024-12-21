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
import json
import logging
import re
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple

from config import config
from game_board.board import DOUBLE_LETTER, DOUBLE_WORDS, TRIPLE_LETTER, TRIPLE_WORDS
from game_board.tiles import bag_as_list, scores

API_VERSION = '1.2'


def board_to_string(board: dict) -> str:
    """Print out Scrabble board dictionary"""
    result = '\n  |' + ' '.join(f'{i + 1:2d}' for i in range(15)) + ' | ' + ' '.join(f'{i + 1:2d}' for i in range(15)) + '\n'
    for row in range(15):
        left = f"{chr(ord('A') + row)} |"
        right = '| '
        for col in range(15):
            cell_key = (col, row)
            cell_value = board.get(cell_key, ('.', '. '))
            left += f' {cell_value[0]} '
            right += f' {cell_value[1]}'
        result += left + right + ' | \n'
    return result


class MoveType(Enum):
    """Enumeration for move types"""

    REGULAR = 1
    PASS_TURN = 2
    EXCHANGE = 3
    WITHDRAW = 4
    CHALLENGE_BONUS = 5
    LAST_RACK_BONUS = 6
    LAST_RACK_MALUS = 7
    TIME_MALUS = 8
    UNKNOWN = 9


class InvalidMoveExeption(Exception):
    """Excpetion for invalid moves"""

    pass


class NoMoveException(Exception):
    """Exception for no move"""

    pass


class Move:  # pylint: disable=too-many-instance-attributes
    """Represents a Move

    After construction, the ``score`` will be calculated

    Attributes:
        type(MoveType): the type of the move
        player(int): active player
        coord((int, int)): coordinates of the move
        is_vertical(bool): vertical move?
        word(str): the current move as string; replaces old tiles with ``.``
        points(int): score for this move
        new_tiles(dict): new tiles in this move
        removed_tiles(dict): removed tiles in this move
        board(dict): current board
        played_time((int, int)): times of the players
        score((int, int)): the scores of the players
        is_scrabble(bool): is this move a scrabble?
        img: the picture of the move (compressed)
        rack(dict,dict): the racks of the players (currently not used)
    """

    def __init__(
        self,
        move_type: MoveType,
        player: int,
        coord: Optional[Tuple[int, int]],
        is_vertical: bool,
        word: str,
        new_tiles: dict,
        removed_tiles: dict,
        board: dict,
        played_time: Tuple[int, int],
        previous_score: Tuple[int, int],
        img=None,
        rack=None,
    ):  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self.type: MoveType = move_type
        self.time: str = str(datetime.now())
        self.move = 0  # set on append of move in class Game
        self.player: int = player
        self.coord: Tuple[int, int] = coord if coord is not None else (-1, -1)
        self.is_vertical = is_vertical
        self.word: str = word
        self.points: int = 0
        self.new_tiles: dict = new_tiles
        self.removed_tiles: dict = removed_tiles
        self.board: dict = board
        self.played_time: Tuple[int, int] = played_time
        self.img = img
        self.modification_cache: dict = {}
        self.rack: Optional[Tuple[dict, dict]] = rack
        if self.type in (MoveType.REGULAR, MoveType.CHALLENGE_BONUS):  # (re) calculate score
            self.points, self.score, self.is_scrabble = self.calculate_score(previous_score)
        else:
            self.score, self.is_scrabble = (previous_score, False)

    def __str__(self) -> str:
        """move as json string"""
        return self.gcg_str()

    def gcg_str(self, nicknames: Optional[Tuple[str, str]] = None) -> str:  # pylint: disable=too-many-branches
        """move as gcg string"""

        mod = f' {chr(0x270F)}' if self.modification_cache else ''  # ✏
        result = f'> {nicknames[self.player]}{mod}: ' if nicknames else f'> Name{self.player}{mod}: '
        if self.type == MoveType.REGULAR:
            (col, row) = self.coord
            result += str(col + 1) + chr(ord('A') + row) if self.is_vertical else chr(ord('A') + row) + str(col + 1)
            gcg_word = ''
            for pos, char in enumerate(self.word):
                if char == '.':
                    if self.is_vertical:
                        gcg_word += f'({self.board[(col, row + pos)][0]})'
                    else:
                        gcg_word += f'({self.board[(col + pos, row)][0]})'
                else:
                    gcg_word += char
            gcg_word = gcg_word.replace(')(', '')
            result += f' {gcg_word} '
        elif self.type in (MoveType.PASS_TURN, MoveType.EXCHANGE):
            result += '- '
        elif self.type == MoveType.WITHDRAW:
            result += '-- '
        elif self.type in (MoveType.LAST_RACK_BONUS, MoveType.LAST_RACK_MALUS):
            result += f'(bank={self.word}) '
        elif self.type == MoveType.CHALLENGE_BONUS:
            result += '(challenge) '
        elif self.type == MoveType.TIME_MALUS:
            result += '(time) '
        elif self.type == MoveType.UNKNOWN:
            result += '(unknown) '
        result += f'{self.points} {self.score[self.player]}'
        return result

    def get_coord(self) -> str:
        """get coord as gcg string"""
        (col, row) = self.coord
        return str(col + 1) + chr(ord('A') + row) if self.is_vertical else chr(ord('A') + row) + str(col + 1)

    def calc_coord(self, coord: str) -> tuple[bool, int, int]:
        """calc coord from gcg string"""
        gcg_coord_h = re.compile('([A-Oa-o])(\\d+)')
        gcg_coord_v = re.compile('(\\d+)([A-Oa-o])')

        col, row = (0, 0)
        vert = False
        if gcg_match := gcg_coord_v.match(coord):
            col = int(gcg_match.group(1)) - 1
            row = int(ord(gcg_match.group(2).capitalize()) - ord('A'))
            vert = True
        if gcg_match := gcg_coord_h.match(coord):
            col = int(gcg_match.group(2)) - 1
            row = int(ord(gcg_match.group(1).capitalize()) - ord('A'))
            vert = False
        return vert, col, row

    def calculate_score(self, previous_score: Tuple[int, int]) -> Tuple[int, Tuple[int, int], bool]:
        """calculate score of the current move"""

        def crossing_points(_pos: Tuple[int, int]) -> int:
            col, row = _pos
            word: str = ''
            if self.is_vertical:
                while col > 0 and (col - 1, row) in self.board:
                    col -= 1
                while col < 15 and (col, row) in self.board:
                    word += self.board[(col, row)][0]
                    col += 1
            else:
                while row > 0 and (col, row - 1) in self.board:
                    row -= 1
                while row < 15 and (col, row) in self.board:
                    word += self.board[(col, row)][0]
                    row += 1
            if len(word) > 1:
                xval = sum(scores(letter) for letter in word)
                if _pos in DOUBLE_LETTER:
                    xval += scores(self.board[pos][0])
                elif _pos in TRIPLE_LETTER:
                    xval += scores(self.board[pos][0]) * 2
                elif _pos in DOUBLE_WORDS:
                    xval *= 2
                elif _pos in TRIPLE_WORDS:
                    xval *= 3
                return xval
            return 0

        if self.board is None or self.type is not MoveType.REGULAR:
            return 0, previous_score, False
        val: int = 0
        crossing_words: int = 0
        letter_bonus: int = 0
        word_bonus: int = 1
        pos: Tuple[int, int] = self.coord
        for i, char in enumerate(self.word):
            if self.board[pos] is None:  # no tile on this board position
                continue
            pos = (self.coord[0], self.coord[1] + i) if self.is_vertical else (self.coord[0] + i, self.coord[1])
            if char != '.':
                crossing_words += crossing_points(pos)  # crossing word
                # check for bonus
                if pos in DOUBLE_LETTER:
                    letter_bonus += scores(self.board[pos][0])
                elif pos in TRIPLE_LETTER:
                    letter_bonus += scores(self.board[pos][0]) * 2
                elif pos in DOUBLE_WORDS:
                    word_bonus *= 2
                elif pos in TRIPLE_WORDS:
                    word_bonus *= 3
                val += scores(self.board[pos][0])
            else:
                val += scores(self.board[pos][0])  # add value of tile
        is_scrabble = len(list(filter(lambda x: x != '.', self.word))) >= 7  # rack empty, so add 50 points
        val += letter_bonus
        val *= word_bonus
        val += crossing_words
        val += 50 if is_scrabble else 0
        score = (
            (previous_score[0] + val, previous_score[1]) if self.player == 0 else (previous_score[0], previous_score[1] + val)
        )
        return val, score, is_scrabble


class Game:
    """Represents the current game"""

    def __init__(self, nicknames: Optional[Tuple[str, str]]):
        self._nicknames: Tuple[str, str] = ('Name1', 'Name2') if nicknames is None else nicknames
        self.gamestart: Optional[datetime] = datetime.now()
        self.moves: List[Move] = []

    def __str__(self) -> str:
        return self.json_str()

    def json_str(self, move_number: int = -1) -> str:
        """Return the json represention of the board"""
        (name1, name2) = self.nicknames
        if len(self.moves) < 1:
            return json.dumps(
                {
                    'api': API_VERSION,
                    'commit': config.git_commit,
                    'layout': config.board_layout,
                    'tournament': config.tournament,
                    'time': str(self.gamestart),
                    'move': 0,
                    'score1': 0,
                    'score2': 0,
                    'time1': config.max_time,
                    'time2': config.max_time,
                    'name1': name1,
                    'name2': name2,
                    'onmove': name1,
                    'moves': [],
                    'board': {},
                    'bag': bag_as_list.copy(),
                }
            )
        move_index = len(self.moves) - 1 if move_number == -1 else move_number - 1
        keys = self.moves[move_index].board.keys()
        values = self.moves[move_index].board.values()
        keys1 = [chr(ord('a') + y) + str(x + 1) for (x, y) in keys]
        values1 = [t for (t, _) in values]
        bag = bag_as_list.copy()
        for i in values1:
            toremove = '_' if i.isalpha() and i.islower() else i
            if toremove in bag:
                bag.remove(toremove)
        gcg_moves = []
        gcg_moves = [self.moves[i].gcg_str(self.nicknames) for i in range(move_index + 1)]
        return json.dumps(
            {
                'api': API_VERSION,
                'commit': config.git_commit,
                'layout': config.board_layout,
                'tournament': config.tournament,
                'time': self.moves[move_index].time,
                'move': self.moves[move_index].move,
                'score1': self.moves[move_index].score[0],
                'score2': self.moves[move_index].score[1],
                'time1': config.max_time - self.moves[move_index].played_time[0],
                'time2': config.max_time - self.moves[move_index].played_time[1],
                'name1': name1,
                'name2': name2,
                'onmove': self.nicknames[self.moves[move_index].player],
                'moves': gcg_moves,
                'board': dict(zip(*[keys1, values1])),
                'bag': bag,
            }
        )

    def dev_str(self) -> str:  # pragma: no cover # pylint: disable=too-many-branches
        """Return devleompemt represention of the game for using in tests"""
        if self.gamestart is None:
            self.gamestart = datetime.now()
        game_id = self.gamestart.strftime('%y%j-%H%M%S')
        out_str = (
            f'game: {game_id}\ngame.ini\n'
            '[default]\n'
            f'warp = {config.video_warp}\n'
            f'name1 = {self.nicknames[0]}\n'
            f'name2 = {self.nicknames[1]}\n'
            f'formatter = {game_id}-{{:d}}.jpg\n'
            f'layout = {config.board_layout}\n'
        )
        if self.moves:
            if self.moves[0].player == 0:
                out_str += 'start = Red\n'  # first move: green
            else:
                out_str += 'start = Green\n'
        if config.video_warp_coordinates:
            out_str += f'warp-coord = {config.video_warp_coordinates}\n'

        out_str += '\ngame.csv\n'
        out_str += 'Move, Button, State, Coord, Word, Points, Score1, Score2\n'
        for move in self.moves:
            if move.player == 0:
                if move.type == MoveType.WITHDRAW:
                    out_str += (
                        f'{move.move}, "Yellow", "P1", "{move.get_coord()}", '
                        f'"{move.word}", {move.points*-1}, {move.score[0]-move.points}, {move.score[1]}\n'
                    )
                    out_str += (
                        f'{move.move}, "DOUBT0", "P1", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                    out_str += (
                        f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                elif move.type == MoveType.CHALLENGE_BONUS:
                    out_str += (
                        f'{move.move}, "Yellow", "P0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                    out_str += (
                        f'{move.move}, "DOUBT1", "P0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                    out_str += (
                        f'{move.move}, "Yellow", "S0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                elif move.type == MoveType.EXCHANGE:
                    out_str += f'{move.move}, "Green", "S1", "-", ' f', {move.points}, {move.score[0]}, {move.score[1]}\n'
                else:
                    out_str += (
                        f'{move.move}, "Green", "S1", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
            else:
                if move.type == MoveType.WITHDRAW:
                    out_str += (
                        f'{move.move}, "Yellow", "P0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points*-1}, {move.score[0]}, {move.score[1]-move.points}\n'
                    )
                    out_str += (
                        f'{move.move}, "DOUBT0", "P0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                    out_str += (
                        f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                elif move.type == MoveType.CHALLENGE_BONUS:
                    out_str += (
                        f'{move.move}, "Yellow", "P1", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                    out_str += (
                        f'{move.move}, "DOUBT0", "P1", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                    out_str += (
                        f'{move.move}, "Yellow", "S1", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                elif move.type == MoveType.EXCHANGE:
                    out_str += f'{move.move}, "Red", "S0", "-", ' f', {move.points}, {move.score[0]}, {move.score[1]}\n'
                elif move.type in (MoveType.LAST_RACK_BONUS, MoveType.LAST_RACK_MALUS):
                    out_str += (
                        f'{move.move}, "EOG", "{("P0", "P1")[move.player]}", "{move.word}", '
                        f', {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
                else:
                    out_str += (
                        f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}\n'
                    )
        return out_str

    def board_str(self, move_index: int = -1) -> str:
        """Return the textual represention of the board"""
        if move_index > len(self.moves):
            return ''
        board = self.moves[move_index].board
        return board_to_string(board=board)

    @property
    def nicknames(self) -> Tuple[str, str]:
        """Return the nicknames (default: Name1, Name2)

        Returns:
            nicknames((str, str)): the player names
        """
        return self._nicknames

    @nicknames.setter
    def nicknames(self, nicknames):
        """Set the nicknames (default: Name1, Name2)

        Arguments:
            nicknames((str, str)): the player names
        """
        self._nicknames = nicknames

    def new_game(self) -> object:
        """Reset to a new game (nicknames, moves)"""
        # with python > 3.11 return type: -> Self
        self.nicknames = ('Name1', 'Name2')
        self.gamestart = datetime.now()
        self.moves.clear()
        return self

    def add_move(self, move: Move) -> object:
        """Add a move to the game

        Args:
            move (Move): The move to add

        Returns:
            self(Game): current game
        """
        # with python > 3.11 return type: -> Self
        self.moves.append(move)
        move.move = len(self.moves)  # set move number
        logging.info(f'add move: #{move.move} player {move.player} points {move.points} score {move.score}')
        return self

    def add_invalid_challenge(self, player: int, played_time: Tuple[int, int]) -> object:
        """Add an invalid challenge to the game

        Args:
            player (int): active player
            played_time (int, int): current player times

        Returns:
            self(Game): current game
        """
        # with python > 3.11 return type: -> Self
        if len(self.moves) < 1:
            raise ValueError('challenge: no previous move available')  # pylint: disable=broad-exception-raised
        last_move = self.moves[-1]
        if last_move.type not in (MoveType.REGULAR, MoveType.CHALLENGE_BONUS, MoveType.UNKNOWN):
            logging.warning(f'(last move {last_move.type.name}): invalid challenge not allowed')
            return self

        logging.debug('scrabble: create move invalid challenge')
        move = copy.deepcopy(last_move)
        move.type = MoveType.CHALLENGE_BONUS
        move.points = config.malus_doubt * -1
        move.player = player
        move.word = ''
        move.removed_tiles = {}
        move.new_tiles = {}
        move.modification_cache = {}
        move.played_time = played_time
        move.score = (
            (move.score[0] - config.malus_doubt, move.score[1])
            if player == 0
            else (move.score[0], move.score[1] - config.malus_doubt)
        )
        self.moves.append(move)
        move.move = len(self.moves)  # set move number
        logging.info(f'invalid challenge: player {move.player} points {move.points} score {move.score}')
        return self

    def add_valid_challenge(self, player: int, played_time: Tuple[int, int]) -> object:
        """Add a valid challenge to the game

        Args:
            player (int): active player
            played_time (int, int): current player times

        Returns:
            self(Game): current game
        """
        # with python > 3.11 return type: -> Self
        if len(self.moves) < 1:
            raise ValueError('challenge: no previous move available')  # pylint: disable=broad-exception-raised
        last_move = self.moves[-1]
        if last_move.type not in (MoveType.REGULAR, MoveType.CHALLENGE_BONUS, MoveType.UNKNOWN):
            logging.warning(f'(last move {last_move.type.name}): valid challenge not allowed')
            return self

        logging.debug('scrabble: create move valid challenge')
        # board information before challenged move
        if len(self.moves) < 2:
            # first move => create move with empty board
            move = Move(MoveType.WITHDRAW, 0, None, False, '', {}, {}, {}, played_time, (0, 0))
        else:
            move = copy.deepcopy(self.moves[-2])  # board, img, score
            move.type = MoveType.WITHDRAW
            move.played_time = played_time
        move.player = 1 if player == 0 else 0
        move.points = -last_move.points
        move.word = last_move.word
        move.removed_tiles = last_move.new_tiles
        move.new_tiles = {}
        move.modification_cache = {}

        self.moves.append(move)
        move.move = len(self.moves)  # set move number
        logging.info(f'valid challenge: player {move.player} points {move.points}')
        return self

    def add_last_rack(self, points: Tuple[int, int], rack_str: str) -> object:
        """Add scpring for the rack at end of game

        Args:
            points (int, int): points for player 0 / 1
            rack_str: remaining rack

        Returns:
            self(Game): current game
        """
        if len(self.moves) > 0:
            last_move = self.moves[-1]
        else:
            last_move = Move(MoveType.UNKNOWN, 0, None, False, '', {}, {}, {}, (0, 0), (0, 0))
        logging.debug('scrabble: create move last rack bonus/malus')

        move = copy.deepcopy(last_move)
        move.type = MoveType.LAST_RACK_BONUS if points[0] > 0 else MoveType.LAST_RACK_MALUS
        move.time = str(datetime.now())
        move.player = 0
        move.word = rack_str
        move.removed_tiles = {}
        move.new_tiles = {}
        move.modification_cache = {}
        move.points = points[0]
        move.score = (move.score[0] + points[0], move.score[1] + points[1])
        move.move = len(self.moves) + 1  # set move number
        self.moves.append(move)

        move = copy.deepcopy(last_move)
        move.type = MoveType.LAST_RACK_MALUS if points[0] > 0 else MoveType.LAST_RACK_BONUS
        move.time = str(datetime.now())
        move.player = 1
        move.word = rack_str
        move.removed_tiles = {}
        move.new_tiles = {}
        move.modification_cache = {}
        move.points = points[1]
        move.score = (move.score[0] + points[0], move.score[1] + points[1])
        move.move = len(self.moves) + 1  # set move number
        self.moves.append(move)

        return self
