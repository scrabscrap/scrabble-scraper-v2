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


class FtpOp(Enum):
    STORE_MOVE = 1
    STORE_ZIP = 2


class FtpStruct:
    def __init__(self, _op: FtpOp, _game: str):
        self.op = _op
        self.game = _game


class FtpThread(Thread):
    def __init__(self, q: Queue):
        self.__queue = q
        Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while True:
            item: FtpStruct = self.__queue.get()
            if item is None:
                self.__queue.task_done()
                break  # reached end of queue
