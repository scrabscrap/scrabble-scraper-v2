"""
 This file is part of the scrabble-scraper distribution (https://github.com/scrabscrap/scrabble-scraper)
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
    regular = 1
    pass_turn = 2
    exchange = 3
    withdraw = 4
    challenge_bonus = 5
    last_rack_bonus = 6
    last_rack_malus = 7
    time_malus = 8
    unknown = 9


class InvalidMoveExeption(Exception):
    pass


class NoMoveException(Exception):
    pass


class Move():
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

    def __init__(self, type: MoveType, player: int, coord: Optional[Tuple[int, int]], is_vertical: bool, word: str,
                 new_tiles: dict, removed_tiles: dict, board: dict, played_time: Tuple[int, int],
                 previous_score: Tuple[int, int], img=None, rack=None):
        self.type: MoveType = type
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
        if self.type in (MoveType.regular, MoveType.challenge_bonus):  # (re) calculate score
            self.score, self.is_scrabble = self._calculate_score(previous_score)
        else:
            self.score, self.is_scrabble = (previous_score, False)

    def __str__(self) -> str:
        # TODO: implement
        return ''

    def json_str(self) -> str:
        """Return the json represention of the move"""
        from state import State

        k = self.board.keys()
        v = self.board.values()
        k1 = [chr(ord('a') + y) + str(x + 1) for (x, y) in k]
        v1 = [t for (t, p) in v]
        bag = bag_as_list.copy()
        [i for i in v1 if i not in bag or bag.remove(i)]  # remove v1 from bag
        (name1, name2) = State().game.nicknames

        to_json = json.dumps(
            {
                'time': self.time,
                'move': self.move,
                'score1': self.score[0],
                'score2': self.score[1],
                'time1': self.played_time[0],
                'time2': self.played_time[1],
                'name1': name1,
                'name2': name2,
                'onmove': self.player,
                'moves': [],
                'board': dict(zip(*[k1, v1])),
                'bag': bag
            })
        return to_json

    def _calculate_score(self, previous_score: Tuple[int, int]) -> Tuple[Tuple[int, int], bool]:

        def crossing_points(pos: Tuple[int, int]) -> int:
            x, y = pos
            word: str = ''
            if self.is_vertical:
                while x > 0 and (x - 1, y) in self.board:
                    x -= 1
                while x < 15 and (x, y) in self.board:
                    word += self.board[(x, y)][0]
                    x += 1
            else:
                while y > 0 and (x, y - 1) in self.board:
                    y -= 1
                while y < 15 and (x, y) in self.board:
                    word += self.board[(x, y)][0]
                    y += 1
            if len(word) > 1:
                xval = sum([scores[letter] for letter in word])
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

        if self.board is None or self.type is not MoveType.regular:
            return (previous_score, False)
        val: int = 0
        crossing_words: int = 0
        letter_bonus: int = 0
        word_bonus: int = 1
        pos: Tuple[int, int] = self.coord
        for i in range(len(self.word)):
            if self.board[pos] is None:  # no tile on this board position
                continue
            if self.is_vertical:
                pos = (self.coord[0], self.coord[1] + i)  # increment rows
            else:
                pos = (self.coord[0] + i, self.coord[1])  # increment cols
            if self.word[i] != '.':
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
        return (score, is_scrabble)


class Game():
    """Represents the current game"""

    def __init__(self, nicknames: Optional[Tuple[str, str]]):
        self._nicknames: Tuple[str, str] = ('Spieler1', 'Spieler2') if nicknames is None else nicknames
        self.moves: List[Move] = []

    def __str__(self) -> str:
        return f'\"nicknames\" : [ \"{self._nicknames[0]}\" , \"{self._nicknames[1]}\" ]'

    def json_str(self) -> str:
        """Return the json represention of the board"""
        return self.__str__()

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
                    result += '- -' if (col, row) in self.moves[-1].removed_tiles else ' . '
            result += ' | '
            for col in range(15):
                result += f' {str(self.moves[-1].board[(col, row)][1])}' if (col, row) in self.moves[-1].board else ' . '
            result += ' | \n'
        return result

    @property
    def nicknames(self) -> Tuple[str, str]:
        """Return the nicknames (default: Spieler1, Spieler2)

        Returns:
            nicknames((str, str)): the player names
        """
        return self._nicknames

    @nicknames.setter
    def nicknames(self, nicknames):
        """Set the nicknames (default: Spieler1, Spieler2)

        Arguments:
            nicknames((str, str)): the player names
        """
        self._nicknames = nicknames

    def new_game(self) -> object:
        """Reset to a new game (nicknames, moves)"""
        # with python > 3.11 return type: -> Self
        self.nicknames = ('Spieler1', 'Spieler2')
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
        return self

    def get_moves(self) -> List[Move]:
        """Return the moves of the current game"""
        return self.moves

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
        if last_move.type not in (MoveType.regular, MoveType.challenge_bonus):
            logging.info(f'(last move {last_move.type.name}): invalid challenge not allowed')
            return self

        logging.debug('scrabble: create move invalid challenge')
        move = copy.deepcopy(last_move)
        move.type = MoveType.challenge_bonus
        move.points = -config.MALUS_DOUBT
        move.player = player
        move.word = ''
        move.removed_tiles = {}
        move.new_tiles = {}
        move.played_time = played_time
        move.score = (move.score[0] - config.MALUS_DOUBT, move.score[1]
                      ) if player == 0 else (move.score[0], move.score[1] - config.MALUS_DOUBT)
        self.moves.append(move)
        move.move = len(self.moves)  # set move number
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
        if last_move.type not in (MoveType.regular, MoveType.challenge_bonus):
            logging.info(f'(last move {last_move.type.name}): valid challenge not allowed')
            return self

        logging.debug('scrabble: create move valid challenge')
        # board information before challenged move
        if len(self.moves) < 2:
            # first move => create move with empty board
            move = Move(MoveType.withdraw, 0, None, False, '', {}, {}, {}, played_time, (0, 0))
        else:
            move = copy.deepcopy(self.moves[-2])  # board, img, score
            move.type = MoveType.withdraw
            move.played_time = played_time
        move.player = 1 if player == 0 else 0
        move.points = -last_move.points
        move.word = last_move.word
        move.removed_tiles = last_move.new_tiles
        move.new_tiles = {}
        self.moves.append(move)
        move.move = len(self.moves)  # set move number
        return self
