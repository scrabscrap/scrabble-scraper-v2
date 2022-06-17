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
from enum import Enum
from queue import Queue
from threading import Thread


class ScrabbleOp(Enum):
    START = 1
    MOVE = 2
    EXCHANGE = 3
    CHALLENGE = 4
    TIME = 5
    QUIT = 6
    RESET = 7


class MoveEnum(Enum):
    REGULAR = 1
    PASS_TURN = 2
    EXCHANGE = 3
    WITHDRAW = 4
    CHALLENGE_BONUS = 5
    LAST_RACK_BONUS = 6
    LAST_RACK_MALUS = 7
    TIME_MALUS = 8
    UNKNOWN = 9


class ScrabbleMove:
    def __init__(self):
        self.type: str = MoveEnum.UNKNOWN.name.lower()
        self.number: int = 0
        self.new_tiles: dict = {'A7': ('I', 75), 'A8': ('R', 75)}
        self.player_name: str = ''
        self.coordinate: str = ''
        self.word: str = ''
        self.player = {'player 1':
                       (('time', 0), ('score_move', 0),
                        ('score', 0), ('rack', '')),
                       'player 2':
                           (('time', 0), ('score_move', 0), ('score', 0), ('rack', ''))}
        self.board: dict = {}
        self.bag: dict = {}
        self.image = None

    # type
    # number
    # zug dict(( (A-O, 1-15)):(tile, prop)) ## ignore new
    # player (nickname)
    # coordinate (A-O 1-15 , A-O 1-15 )
    # word
    # player[0/1]
    #  (time, score move, score player, rack)
    # board : dict (A-O, 1-15)
    # bag : dict (A-O, 1-15)
    # image


class ScrabbleGame:
    def __init__(self):
        pass

    # player1 - name
    # player2 - name
    # move[]


class ScrabbleStruct:
    def __init__(self, _op: ScrabbleOp, _img, _active, _scrabble, _time):
        # operation
        # timestamp
        # player
        # image
        # copy of game
        self.op = _op  # move, --, challenge, time
        self.img = _img


class ScrabbleThread(Thread):

    def __init__(self, q: Queue):
        self.__queue = q
        Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while True:
            item = self.__queue.get()
            if item is None:
                self.__queue.task_done()
                break  # reached end of queue
