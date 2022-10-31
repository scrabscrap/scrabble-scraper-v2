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
from abc import abstractmethod


class Display:
    """ display abstract implementation """

    def __init__(self):
        pass

    @abstractmethod
    def stop(self) -> None:
        """ power off display """
        logging.debug('stop')

    @abstractmethod
    def show_boot(self) -> None:
        """ show boot messsage """
        logging.debug('add boot')

    @abstractmethod
    def show_reset(self) -> None:
        """ show reset message """
        logging.debug('add reset')

    @abstractmethod
    def show_ready(self, msg=('Ready', 'Ready')) -> None:
        """ show ready message """
        logging.debug(f'add ready => {msg[0] - msg[1]}')

    @abstractmethod
    def show_pause(self, player: int) -> None:
        """" show pause message """
        logging.debug('add pause')

    @abstractmethod
    def add_malus(self, player: int) -> None:
        """ show malus message """
        logging.debug(f'add malus on {player}')

    @abstractmethod
    def add_remove_tiles(self, player: int) -> None:
        """ show remove tiles message """
        logging.debug(f'add remove tiles on {player}')

    @abstractmethod
    def add_doubt_timeout(self, player: int) -> None:
        """ show doubt timeout marker """
        logging.debug(f'doubt timeout for player {player}')

    @abstractmethod
    def show_cam_err(self) -> None:
        """ show camera error message """
        logging.debug('add cam err')

    @abstractmethod
    def show_ftp_err(self) -> None:
        """" show ftp error message """
        logging.debug('add cam err')

    @abstractmethod
    def show_config(self) -> None:
        """ show config message """
        logging.debug('add config')

    @abstractmethod
    def add_time(self, player: int, time1: int, played1: int, time2: int, played2: int) -> None:
        """" show timer message """
        # m1, s1 = divmod(abs(1800 - t1), 60)
        # m2, s2 = divmod(abs(1800 - t2), 60)
        # doubt1 = 'x' if player == 0 and p1 <= 300 else ' '
        # doubt2 = 'x' if player == 1 and p2 <= 300 else ' '
        # left = f'{doubt1} -{m1:1d}:{s1:02d} ({p1:4d})' if 1800 - \
        #     t1 < 0 else f'{doubt1} {m1:02d}:{s1:02d} ({p1:4d})'
        # right = f'{doubt2} -{m2:1d}:{s2:02d} ({p2:4d})' if 1800 - \
        #     t2 < 0 else f'{doubt2} {m2:02d}:{s2:02d} ({p2:4d})'
        # logging.debug(f'add time {left} / {right}')
        pass

    @abstractmethod
    def clear_message(self, player=None) -> None:
        """ clear display """
        pass

    @abstractmethod
    def clear(self) -> None:
        """ clear message strings """
        logging.debug('clear')

    @abstractmethod
    def show(self, player=None, invert=None) -> None:
        """ show display content """
        pass
