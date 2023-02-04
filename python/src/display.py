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
from typing import Optional

from config import config
from scrabble import Game


class Display:
    """ display abstract implementation """

    def __init__(self):
        pass

    @abstractmethod
    def stop(self) -> None:
        """Poweroff display"""
        logging.debug('display stop')

    @abstractmethod
    def show_boot(self, current_ip=('', '')) -> None:
        """show boot message"""
        logging.debug('Boot message')

    @abstractmethod
    def show_reset(self) -> None:
        """show reset message"""
        logging.debug('Reset message')

    @abstractmethod
    def show_accesspoint(self) -> None:
        """show AP Mode message"""
        logging.debug('AP Mode message')

    @abstractmethod
    def show_ready(self, msg=('Ready', 'Ready')) -> None:
        """show ready message"""
        logging.debug('Ready message')

    @abstractmethod
    def show_end_of_game(self) -> None:
        """show ready message"""
        logging.debug('end of game message')

    @abstractmethod
    def show_pause(self, player: int, played_time: list[int], current: list[int]) -> None:
        """show pause hint"""
        assert player in [0, 1], "invalid player number"
        logging.debug('Pause message')

    @abstractmethod
    def add_malus(self, player: int, played_time: list[int], current: list[int]) -> None:
        """show malus hint"""
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: malus -10')

    @abstractmethod
    def add_remove_tiles(self, player: int, played_time: list[int], current: list[int]) -> None:
        """show remove tiles"""
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: Entf. Zug')

    @abstractmethod
    def add_doubt_timeout(self, player: int, played_time: list[int], current: list[int]) -> None:
        """show error on doubt: timeout"""
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: doubt timeout')

    @abstractmethod
    def show_cam_err(self) -> None:
        """show cam error"""
        logging.debug('Cam err message')

    @abstractmethod
    def show_ftp_err(self) -> None:
        """show ftp error"""
        logging.debug('FTP err message')

    @abstractmethod
    def show_config(self) -> None:
        """show config message"""
        logging.debug('Cfg message')

    @abstractmethod
    def set_game(self, game: Game) -> None:
        """set current game to display scores"""
        pass

    @abstractmethod
    def render_display(self, player: int, played_time: list[int], current: list[int], info: Optional[str] = None) -> None:
        """render display content"""
        assert player in [0, 1], "invalid player number"

        minutes, seconds = divmod(abs(config.max_time - played_time[player]), 60)
        text = f'-{minutes:1d}:{seconds:02d}' if config.max_time - played_time[player] < 0 else f'{minutes:02d}:{seconds:02d}'
        logging.debug(f'render_display {player}: {text}')
