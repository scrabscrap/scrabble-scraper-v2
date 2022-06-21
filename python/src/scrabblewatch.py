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
import time
from threading import Event, Thread
from typing import Optional

from mockdisplay import MockDisplay

from config import config
from oled import OledDisplay


class RepeatedTimer:

    def __init__(self, interval: int, function: callable, *args, **kwargs):  # type: ignore
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target)
        self.thread.start()

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self):
        """ stops the RepeatedTimer """
        self.event.set()
        self.thread.join()


class ScrabbleWatch:

    def __init__(self):
        self.play_time: int = 0
        self.time: list[int] = [0, 0]
        self.current: list[int] = [0, 0]
        self.paused: bool = True
        self.player: int = 0  # 0/1 ... player 1/player 2
        self.display = OledDisplay()  # todo: use factory
        self.timer = RepeatedTimer(1, self.tick)

    def start(self, player: int):
        self.display.clear_message(self.player)
        self.play_time = 0
        self.player = player
        self.time = [0, 0]
        self.current = [0, 0]
        self.paused = False

    def pause(self):
        self.paused = True
        self.display.show_pause(self.player)

    def resume(self):
        self.display.clear_message()
        self.paused = False

    def reset(self):
        self.paused = True
        self.play_time = 0
        self.time = [0, 0]
        self.current = [0, 0]
        self.player = 0

    def tick(self):
        self.play_time += 1
        if not self.paused:
            self.time[self.player] += 1
            self.current[self.player] += 1
            self.display.add_time(self.player,
                                  self.time[0], self.current[0], self.time[1], self.current[1])
            self.display.show()

    def get_status(self) -> tuple[int, int, int, int, int]:
        """ returns: active_player
            played_time(player1), time_current_move(player1),
            played_time(player2), time_current_move(player2) """
        return self.player, self.time[0], self.current[0], self.time[1], self.current[1]
