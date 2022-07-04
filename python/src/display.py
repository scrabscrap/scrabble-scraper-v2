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
from abc import abstractmethod


class Display:

    @abstractmethod
    def stop(self) -> None:
        logging.debug('stop')
        pass

    @abstractmethod
    def show_boot(self) -> None:
        logging.debug('add boot')
        pass

    @abstractmethod
    def show_reset(self) -> None:
        logging.debug('add reset')
        pass

    @abstractmethod
    def show_ready(self) -> None:
        logging.debug('add ready')
        pass

    @abstractmethod
    def show_pause(self, player: int) -> None:
        logging.debug('add pause')
        pass

    @abstractmethod
    def add_malus(self, player: int) -> None:
        logging.debug(f'add malus on {player}')
        pass

    @abstractmethod
    def add_remove_tiles(self, player: int) -> None:
        logging.debug(f'add remove tiles on {player}')
        pass

    @abstractmethod
    def show_cam_err(self) -> None:
        logging.debug('add cam err')
        pass

    @abstractmethod
    def show_ftp_err(self) -> None:
        logging.debug('add cam err')
        pass

    @abstractmethod
    def show_config(self) -> None:
        logging.debug('add config')
        pass

    @abstractmethod
    def add_time(self, player: int, t1: int, p1: int, t2: int, p2: int) -> None:
        m1, s1 = divmod(abs(1800 - t1), 60)
        m2, s2 = divmod(abs(1800 - t2), 60)
        doubt1 = 'x' if player == 0 and p1 <= 300 else ' '
        doubt2 = 'x' if player == 1 and p2 <= 300 else ' '
        left = f'{doubt1} -{m1:1d}:{s1:02d} ({p1:4d})' if 1800 - \
            t1 < 0 else f'{doubt1} {m1:02d}:{s1:02d} ({p1:4d})'
        right = f'{doubt2} -{m2:1d}:{s2:02d} ({p2:4d})' if 1800 - \
            t2 < 0 else f'{doubt2} {m2:02d}:{s2:02d} ({p2:4d})'
        logging.debug(f'add time {left} / {right}')
        pass

    @abstractmethod
    def clear_message(self, player=None) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        logging.debug('clear')
        pass

    @abstractmethod
    def show(self, player=None, invert=None) -> None:
        pass
