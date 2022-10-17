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
import logging
import time
from concurrent.futures import Future
from threading import Event


class RepeatedTimer:
    def __init__(self, interval: int, function: callable):  # type: ignore
        self.interval = interval
        self.function = function
        self.event = None
        self.start = time.time()

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def tick(self, ev: Event) -> None:
        self.event = ev
        while not ev.wait(self._time):
            self.function()
        ev.clear()

    def cancel(self) -> None:
        if self.event is not None:
            self.event.set()

    def done(self, result: Future) -> None:
        logging.info(f'timer done {result}')
        pass
