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
from typing import Optional

from util import Singleton

try:
    from hardware.oled import PlayerDisplay
except ImportError:
    logging.warning('use mock as PlayerDisplay')
    from display import Display as PlayerDisplay


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
        self.display.clear_message(self.player)
        self.display.show(self.player)
        self.play_time = 0
        self.player = player
        self.current = [0, 0]
        self.paused = False

    def pause(self) -> None:
        """pause timer"""
        self.paused = True
        self.display.show_pause(self.player)

    def resume(self) -> None:
        """resume timer"""
        self.paused = False
        self.display.show(invert=False)

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
            self.display.add_time(self.player, self.time[0], self.current[0], self.time[1], self.current[1])
            self.display.show(self.player)

    def get_status(self) -> tuple[int, int, int, int, int]:
        """ get current timer status

            Returns
                player (int): current player
                time1 (int): time player 1
                current1 (int): time player 1 on current move
                time2 (int): time player 2
                current3 (int): time player 2 on current move
        """
        return self.player, self.time[0], self.current[0], self.time[1], self.current[1]
