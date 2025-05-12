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

import threading
import time


class RepeatedTimer(threading.Timer):
    """create a timer thread with a specific intervall"""

    def run(self):
        start_timer = time.time()
        to_wait = self.interval
        while not self.finished.wait(to_wait):
            self.function(*self.args, **self.kwargs)
            to_wait = self.interval - ((time.time() - start_timer) % self.interval)
