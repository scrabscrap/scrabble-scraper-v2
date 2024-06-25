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
from typing import Optional, Protocol

from config import config
from scrabble import Game


class Display(Protocol):
    """Display to show timer and events"""

    def stop(self) -> None:
        """Poweroff display"""

    def show_boot(self) -> None:
        """show boot message"""

    def show_reset(self) -> None:
        """show reset message"""

    def show_accesspoint(self) -> None:
        """show AP Mode message"""

    def show_ready(self, msg: tuple[str, str] = ('Ready', 'Ready')) -> None:
        """show ready message

        Parameters:
            msg(tuple[str, str]): message to show - default=('Ready', 'Ready')
        """

    def show_end_of_game(self) -> None:
        """show ready message"""

    def show_pause(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        """show pause hint

        Parameters:
            player(int): show pause for player
            played_time(tuple[int, int]): played time to display
            current(tuple[int, int]): time for current move
        """

    def add_malus(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        """show malus hint

        Parameters:
            player(int): show message for player
            played_time(tuple[int, int]): played time to display
            current(tuple[int, int]): time for current move
        """

    def add_remove_tiles(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        """show remove tiles

        Parameters:
            player(int): show message for player
            played_time(tuple[int, int]): played time to display
            current(tuple[int, int]): time for current move
        """

    def add_doubt_timeout(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        """show error on doubt: timeout

        Parameters:
            player(int): show message for player
            played_time(tuple[int, int]): played time to display
            current(tuple[int, int]): time for current move
        """

    def show_cam_err(self) -> None:
        """show cam error"""

    def show_ftp_err(self) -> None:
        """show ftp error"""

    def set_game(self, game: Game) -> None:
        """set current game to display scores

        Parameters:
            game(Game): game to set
        """

    def render_display(
        self, player: int, played_time: tuple[int, int], current: tuple[int, int], info: Optional[str] = None
    ) -> None:
        """render display content

        Parameters:
            player(int): show message for player
            played_time(tuple[int, int]): played time to display
            current(tuple[int, int]): time for current move
            info(str): additional string to display
        """


class DisplayMock(Display):
    """display abstract implementation"""

    def __init__(self) -> None:
        self.lastplayer: int = -1
        super().__init__()

    def stop(self) -> None:
        logging.debug('display stop')

    def show_boot(self) -> None:
        logging.debug('Boot message')

    def show_reset(self) -> None:
        logging.debug('Reset message')

    def show_accesspoint(self) -> None:
        logging.debug('AP Mode message')

    def show_ready(self, msg=('Ready', 'Ready')) -> None:
        logging.debug(f'Ready message: {msg}')

    def show_end_of_game(self) -> None:
        logging.debug('end of game message')

    def show_pause(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        assert player in {0, 1}, 'invalid player number'
        logging.debug(f'Pause message: {player}/{played_time}/{current}')

    def add_malus(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        assert player in {0, 1}, 'invalid player number'
        logging.debug(f'{player}: malus -10: {played_time}/{current}')

    def add_remove_tiles(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        assert player in {0, 1}, 'invalid player number'
        logging.debug(f'{player}: Entf. Zug: {played_time}/{current}')

    def add_doubt_timeout(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        assert player in {0, 1}, 'invalid player number'
        logging.debug(f'{player}: doubt timeout: {played_time}/{current}')

    def show_cam_err(self) -> None:
        logging.debug('Cam err message')

    def show_ftp_err(self) -> None:
        logging.debug('FTP err message')

    def set_game(self, game: Game) -> None:
        pass

    def render_display(
        self, player: int, played_time: tuple[int, int], current: tuple[int, int], info: Optional[str] = None
    ) -> None:
        assert player in {0, 1}, 'invalid player number'

        minutes, seconds = divmod(abs(config.max_time - played_time[player]), 60)
        text = f'-{minutes:1d}:{seconds:02d}' if config.max_time - played_time[player] < 0 else f'{minutes:02d}:{seconds:02d}'
        # log message only if player changed
        if self.lastplayer != player:
            logging.debug(f'render_display {player}: {text} ({current}/{info})')
            self.lastplayer = player
