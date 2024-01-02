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

from display import Display
from util import Static

try:
    os.stat('/dev/i2c-1')
    os.stat('/dev/i2c-3')
    from hardware.oled import PlayerDisplay as DisplayImpl
except (FileNotFoundError, ImportError):
    logging.warning('no i2c device found or import error')
    from display import DisplayMock as DisplayImpl  # type: ignore # pylint: disable=ungrouped-imports


class ScrabbleWatch(Static):
    """timer for played time"""
    play_time: int = 0
    time: tuple[int, int] = (0, 0)
    current: tuple[int, int] = (0, 0)
    paused: bool = True
    player: int = 0  # 0/1 ... player 1/player 2
    display: Display = DisplayImpl()

    @classmethod
    def start(cls, player: int) -> None:
        """start timer"""
        last = cls.player
        cls.play_time = 0
        cls.player = player
        cls.current = (0, 0)
        cls.paused = False
        cls.display.render_display(last, cls.time, cls.current)

    @classmethod
    def pause(cls) -> None:
        """pause timer"""
        cls.paused = True
        cls.display.show_pause(cls.player, cls.time, cls.current)

    @classmethod
    def resume(cls) -> None:
        """resume timer"""
        cls.paused = False

    @classmethod
    def reset(cls) -> None:
        """reset timer"""
        cls.paused = True
        cls.display.show_reset()
        cls.play_time = 0
        cls.time = (0, 0)
        cls.current = (0, 0)
        cls.player = 0

    @classmethod
    def tick(cls) -> None:
        """add one second"""
        cls.play_time += 1
        if not cls.paused:
            cls.time = (cls.time[0] + 1, cls.time[1]) if cls.player == 0 else (cls.time[0], cls.time[1] + 1)
            cls.current = (cls.current[0] + 1, cls.current[1]) if cls.player == 0 else (cls.current[0], cls.current[1] + 1)
            cls.display.render_display(cls.player, cls.time, cls.current)

    @classmethod
    def status(cls) -> tuple[int, tuple[int, int], tuple[int, int]]:
        """ get current timer status

            Returns
                player (int): current player
                time (int, int): time player 1,2
                current (int, int): time player 1,2 on current move
        """
        return cls.player, cls.time, cls.current
