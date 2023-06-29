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

from config import config
from scrabble import Game

from util import Static


class Display(Static):
    """ display abstract implementation """
    lastplayer: int = -1

    @classmethod
    def stop(cls) -> None:
        """Poweroff display"""
        logging.debug('display stop')

    @classmethod
    def show_boot(cls, current_ip=('', '')) -> None:
        """show boot message"""
        logging.debug('Boot message')

    @classmethod
    def show_reset(cls) -> None:
        """show reset message"""
        logging.debug('Reset message')

    @classmethod
    def show_accesspoint(cls) -> None:
        """show AP Mode message"""
        logging.debug('AP Mode message')

    @classmethod
    def show_ready(cls, msg=('Ready', 'Ready')) -> None:
        """show ready message"""
        logging.debug('Ready message')

    @classmethod
    def show_end_of_game(cls) -> None:
        """show ready message"""
        logging.debug('end of game message')

    @classmethod
    def show_pause(cls, player: int, played_time: list[int], current: list[int]) -> None:
        """show pause hint"""
        assert player in [0, 1], "invalid player number"
        logging.debug('Pause message')

    @classmethod
    def add_malus(cls, player: int, played_time: list[int], current: list[int]) -> None:
        """show malus hint"""
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: malus -10')

    @classmethod
    def add_remove_tiles(cls, player: int, played_time: list[int], current: list[int]) -> None:
        """show remove tiles"""
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: Entf. Zug')

    @classmethod
    def add_doubt_timeout(cls, player: int, played_time: list[int], current: list[int]) -> None:
        """show error on doubt: timeout"""
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: doubt timeout')

    @classmethod
    def show_cam_err(cls) -> None:
        """show cam error"""
        logging.debug('Cam err message')

    @classmethod
    def show_ftp_err(cls) -> None:
        """show ftp error"""
        logging.debug('FTP err message')

    @classmethod
    def show_config(cls) -> None:
        """show config message"""
        logging.debug('Cfg message')

    @classmethod
    def set_game(cls, game: Game) -> None:
        """set current game to display scores"""
        pass

    @classmethod
    def render_display(cls, player: int, played_time: list[int], current: list[int], info: Optional[str] = None) -> None:
        """render display content"""
        assert player in [0, 1], "invalid player number"

        minutes, seconds = divmod(abs(config.max_time - played_time[player]), 60)
        text = f'-{minutes:1d}:{seconds:02d}' if config.max_time - played_time[player] < 0 else f'{minutes:02d}:{seconds:02d}'
        # log message only if player changed
        if cls.lastplayer != player:
            logging.debug(f'render_display {player}: {text}')
            cls.lastplayer = player
