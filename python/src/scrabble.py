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
import datetime
import json
import logging
from enum import Enum
from typing import List, Optional, Tuple

from config import config
from game_board.board import (DOUBLE_LETTER, DOUBLE_WORDS, TRIPLE_LETTER,
                              TRIPLE_WORDS)
from game_board.tiles import bag_as_list, scores


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


class Move:  # pylint: disable=R0902 # too-many-instance-attributes
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

    def __init__(self, move_type: MoveType, player: int,  # pylint: disable=R0913 # too-many-arguments
                 coord: Optional[Tuple[int, int]], is_vertical: bool, word: str, new_tiles: dict, removed_tiles: dict,
                 board: dict, played_time: Tuple[int, int], previous_score: Tuple[int, int], img=None, rack=None):
        self.type: MoveType = move_type
        self.time: str = str(datetime.datetime.now())
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
        self.rack: Optional[Tuple[dict, dict]] = rack
        if self.type in (MoveType.REGULAR, MoveType.CHALLENGE_BONUS):  # (re) calculate score
            self.points, self.score, self.is_scrabble = self.calculate_score(previous_score)
        else:
            self.score, self.is_scrabble = (previous_score, False)

    def __str__(self) -> str:
        """move as json string"""
        return self.gcg_str()

    def gcg_str(self, nicknames: Optional[Tuple[str, str]] = None) -> str:
        """move as gcg string"""

        if nicknames:
            result = f'> {nicknames[self.player]}: '
        else:
            result = f'> Name{self.player}: '
        if self.type == MoveType.REGULAR:
            (col, row) = self.coord
            result += str(col + 1) + chr(ord('A') + row) if self.is_vertical else chr(
                ord('A') + row) + str(col + 1)
            result += f' {self.word} '
        elif self.type == MoveType.PASS_TURN:
            result += "- "
        elif self.type == MoveType.EXCHANGE:
            result += "- "  # f'- {self.exchange} '
        elif self.type == MoveType.WITHDRAW:
            result += "-- "
        # elif self.type == MoveType.last_rack_bonus:
        #     result += f'({self.opp_rack}) '
        # elif self.type == MoveType.last_rack_malus:
        #     result += f'({self.rack}) '
        elif self.type == MoveType.CHALLENGE_BONUS:
            result += "(challenge) "
        elif self.type == MoveType.TIME_MALUS:
            result += "(time) "
        elif self.type == MoveType.UNKNOWN:
            result += "(unknown) "
        result += f"{self.points:+d} {self.score[self.player]:+d}"
        return result

    def calculate_score(self, previous_score: Tuple[int, int]) -> Tuple[int, Tuple[int, int], bool]:
        """calculate score of the current move"""
        def crossing_points(pos: Tuple[int, int]) -> int:
            col, row = pos
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
                xval = sum(scores[letter] for letter in word)
                if pos in DOUBLE_LETTER:
                    xval += scores[self.board[pos][0]]
                elif pos in TRIPLE_LETTER:
                    xval += scores[self.board[pos][0]] * 2
                elif pos in DOUBLE_WORDS:
                    xval *= 2
                elif pos in TRIPLE_WORDS:
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
                    letter_bonus += scores[self.board[pos][0]]
                elif pos in TRIPLE_LETTER:
                    letter_bonus += scores[self.board[pos][0]] * 2
                elif pos in DOUBLE_WORDS:
                    word_bonus *= 2
                elif pos in TRIPLE_WORDS:
                    word_bonus *= 3
                val += scores[self.board[pos][0]]
            else:
                val += scores[self.board[pos][0]]  # add value of tile
        is_scrabble = len(list(filter(lambda x: x != '.', self.word))) >= 7  # rack empty, so add 50 points
        val += letter_bonus
        val *= word_bonus
        val += crossing_words
        val += 50 if is_scrabble else 0
        score = (previous_score[0] + val, previous_score[1]
                 ) if self.player == 0 else (previous_score[0], previous_score[1] + val)
        return val, score, is_scrabble


class Game():
    """Represents the current game"""

    def __init__(self, nicknames: Optional[Tuple[str, str]]):
        self._nicknames: Tuple[str, str] = ('Name1', 'Name2') if nicknames is None else nicknames
        self.gamestart: Optional[datetime.datetime] = datetime.datetime.now()
        self.moves: List[Move] = []

    def __str__(self) -> str:
        return self.json_str()

    def json_str(self, move_number: int = -1) -> str:
        """Return the json represention of the board"""
        if len(self.moves) < 1:
            return '{}'
        move_index = len(self.moves) - 1 if move_number == -1 else move_number - 1
        keys = self.moves[move_index].board.keys()
        values = self.moves[move_index].board.values()
        keys1 = [chr(ord('a') + y) + str(x + 1) for (x, y) in keys]
        values1 = [t for (t, p) in values]
        bag = bag_as_list.copy()
        _ = [i for i in values1 if i not in bag or bag.remove(i)]  # type: ignore # side effect remove v1 from bag
        (name1, name2) = self.nicknames

        gcg_moves = []
        for i in range(0, move_index + 1):
            gcg_moves.append(self.moves[i].gcg_str(self.nicknames))
        to_json = json.dumps(
            {
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
                'bag': bag
            })
        return to_json

    def board_str(self) -> str:
        """Return the textual represention of the board"""
        result = '  |'
        for i in range(15):
            result += f'{(i + 1):2d} '
        result += ' | '
        for i in range(15):
            result += f'{(i + 1):2d} '
        result += '\n'
        for row in range(15):
            result += f"{chr(ord('A') + row)} |"
            for col in range(15):
                if (col, row) in self.moves[-1].board:
                    result += f'[{self.moves[-1].board[(col, row)][0]}]' \
                        if (col, row) in self.moves[-1].new_tiles else f' {self.moves[-1].board[(col, row)][0]} '
                else:
                    result += ' - ' if (col, row) in self.moves[-1].removed_tiles else ' . '
            result += ' | '
            for col in range(15):
                result += f' {str(self.moves[-1].board[(col, row)][1])}' if (col, row) in self.moves[-1].board else ' . '
            result += ' | \n'
        return result

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
        self.gamestart = datetime.datetime.now()
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
            raise Exception('challenge: no previous move available')
        last_move = self.moves[-1]
        if last_move.type not in (MoveType.REGULAR, MoveType.CHALLENGE_BONUS):
            logging.warning(f'(last move {last_move.type.name}): invalid challenge not allowed')
            return self

        logging.debug('scrabble: create move invalid challenge')
        move = copy.deepcopy(last_move)
        move.type = MoveType.CHALLENGE_BONUS
        move.points = -config.malus_doubt
        move.player = player
        move.word = ''
        move.removed_tiles = {}
        move.new_tiles = {}
        move.played_time = played_time
        move.score = (move.score[0] - config.malus_doubt, move.score[1]
                      ) if player == 0 else (move.score[0], move.score[1] - config.malus_doubt)
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
            raise Exception('challenge: no previous move available')
        last_move = self.moves[-1]
        if last_move.type not in (MoveType.REGULAR, MoveType.CHALLENGE_BONUS):
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
        self.moves.append(move)
        move.move = len(self.moves)  # set move number
        logging.info(f'valid challenge: player {move.player} points {move.points}')
        return self
