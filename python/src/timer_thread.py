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
from typing import Callable, Optional


class RepeatedTimer:
    """create a timer thread with a specific intervall"""

    def __init__(self, interval: int, function: Callable):  # type: ignore
        self.interval = interval
        self.function = function
        self.event: Optional[Event] = None
        self.start = time.time()

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def tick(self, event: Event) -> None:
        """call funtion on every tick"""
        self.event = event
        while not event.wait(self._time):
            try:
                self.function()
            except Exception as oops:  # pylint: disable=broad-exception-caught
                # ignore all exceptions in self.function
                logging.warning(f'Exception in timed function {oops}')
        event.clear()

    def cancel(self) -> None:
        """cancel timer thread"""
        if self.event is not None:
            self.event.set()

    def done(self, result: Future) -> None:
        """end of timer thread"""
        logging.info(f'timer done {result}')
