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
import os
from typing import Optional

from util import Singleton

try:
    os.stat('/dev/i2c-1')
    from hardware.oled import PlayerDisplay
except (FileNotFoundError, ImportError):
    logging.warning('no i2c device found or import error')
    from display import Display as PlayerDisplay  # type: ignore


class ScrabbleWatch(metaclass=Singleton):
    """timer for played time"""
    from display import Display

    def __init__(self, _display: Optional[Display] = None):
        self.play_time: int = 0
        self.time: list[int] = [0, 0]
        self.current: list[int] = [0, 0]
        self.paused: bool = True
        self.player: int = 0  # 0/1 ... player 1/player 2
        if _display is not None:
            self.display = _display
        else:
            self.display = PlayerDisplay()  # default

    def start(self, player: int) -> None:
        """start timer"""
        last = self.player
        self.play_time = 0
        self.player = player
        self.current = [0, 0]
        self.paused = False
        self.display.render_display(last, self.time, self.current)

    def pause(self) -> None:
        """pause timer"""
        self.paused = True
        self.display.show_pause(self.player, self.time, self.current)

    def resume(self) -> None:
        """resume timer"""
        self.paused = False

    def reset(self) -> None:
        """reset timer"""
        self.paused = True
        self.display.show_reset()
        self.play_time = 0
        self.time = [0, 0]
        self.current = [0, 0]
        self.player = 0

    def tick(self) -> None:
        """add one second"""
        self.play_time += 1
        if not self.paused:
            self.time[self.player] += 1
            self.current[self.player] += 1
            self.display.render_display(self.player, self.time, self.current)

    def status(self) -> tuple[int, list[int], list[int]]:
        """ get current timer status

            Returns
                player (int): current player
                time (int, int): time player 1,2
                current (int, int): time player 1,2 on current move
        """
        return self.player, self.time, self.current
