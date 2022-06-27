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
import logging
from enum import Enum
from queue import Queue
from threading import Thread


class ScrabbleOp(Enum):
    START = 0
    MOVE = 1
    EXCHANGE = 2
    VALID_CHALLANGE = 3
    INVALID_CHALLANGE = 4
    RESET_GAME = 5
    QUIT_GAME = 6


class ScrabbleOpStruct:
    def __init__(self, _op: ScrabbleOp, _img, _game: str):
        self.op = _op
        self.img = _img
        self.game = _game


class ScrabbleOpQueue(Thread):
    def __init__(self, q: Queue):
        self.__queue = q
        Thread.__init__(self)
        self.setName('EventThread')
        self.setDaemon(True)

    def run(self):
        while True:
            item: ScrabbleOpStruct = self.__queue.get()
            if item is None:
                self.__queue.task_done()
                break  # reached end of queue
            if item.op is ScrabbleOp.MOVE:
                logging.debug(f'Move: ')
            if item.op is ScrabbleOp.VALID_CHALLANGE:
                logging.debug(f'Valid Challange: ')
            if item.op is ScrabbleOp.INVALID_CHALLANGE:
                logging.debug(f'Invalid Challange: ')
            if item.op is ScrabbleOp.RESET_GAME:
                logging.debug(f'Reset game: ')
            self.__queue.task_done()
            logging.debug('scrabble task finished')
