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

from __future__ import annotations

import logging

from config import config
from scrabble import Game


class Display:
    """Display to show timer and events"""

    def __init__(self) -> None:
        self.lastplayer: int = -1
        self.game: Game | None = None

    def stop(self) -> None:
        """Poweroff display"""
        logging.debug('display stop')

    def show_boot(self) -> None:
        """show boot message"""
        self.show_ready(('Loading\u2026', 'Loading\u2026'))

    def show_accesspoint(self) -> None:
        """show AP Mode message"""
        self.show_ready(('AP Mode', 'AP Mode'))

    def show_ready(self, msg: tuple[str, str] = ('Ready', 'Ready')) -> None:
        """show ready message

        Parameters:
            msg(tuple[str, str]): message to show - default=('Ready', 'Ready')
        """
        logging.debug(f'Ready message: {msg}')

    def show_end_of_game(self) -> None:
        """show ready message"""
        logging.debug('end of game message')
        if self.game and self.game.moves:
            for i in range(2):
                nickname = self.game.nicknames[i][:10]
                minutes, seconds = divmod(abs(config.scrabble.max_time - self.game.moves[-1].played_time[i]), 60)
                score = self.game.moves[-1].score[i]
                logging.debug(f'{nickname} {score} {minutes:02d}:{seconds:02d}')

    def show_pause(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        """show pause hint

        Parameters:
            player(int): show pause for player
            played_time(tuple[int, int]): played time to display
            current(tuple[int, int]): time for current move
        """
        logging.debug('Pause message')
        msg = 'Pause'
        if config.scrabble.show_score and self.game and len(self.game.moves):
            msg = f'P {self.game.moves[-1].score[player]:3d}'
        self.render_display(player, played_time, current, msg)

    def add_malus(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        """show malus hint

        Parameters:
            player(int): show message for player
            played_time(tuple[int, int]): played time to display
            current(tuple[int, int]): time for current move
        """
        self.render_display(player, played_time, current, '-10P')

    def add_remove_tiles(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        """show remove tiles

        Parameters:
            player(int): show message for player
            played_time(tuple[int, int]): played time to display
            current(tuple[int, int]): time for current move
        """
        self.render_display(player, played_time, current, '\u2717Zug\u270d')

    def add_doubt_timeout(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        """show error on doubt: timeout

        Parameters:
            player(int): show message for player
            played_time(tuple[int, int]): played time to display
            current(tuple[int, int]): time for current move
        """
        self.render_display(player, played_time, current, '\u21afZeit')

    def show_cam_err(self) -> None:
        """show cam error"""
        self.show_ready(('\u2620 Cam err', '\u2620 Cam err'))

    def show_ftp_err(self) -> None:
        """show ftp error"""
        self.show_ready(('\u2620 FTP err', '\u2620 FTP err'))

    def set_game(self, game: Game) -> None:
        """set current game to display scores

        Parameters:
            game(Game): game to set
        """
        self.game = game

    def render_display(
        self, player: int, played_time: tuple[int, int], current: tuple[int, int], info: str | None = None
    ) -> None:
        """render display content

        Parameters:
            player(int): show message for player
            played_time(tuple[int, int]): played time to display
            current(tuple[int, int]): time for current move
            info(str): additional string to display
        """
        minutes, seconds = divmod(abs(config.scrabble.max_time - played_time[player]), 60)
        text = (
            f'-{minutes:1d}:{seconds:02d}'
            if config.scrabble.max_time - played_time[player] < 0
            else f'{minutes:02d}:{seconds:02d}'
        )
        # log message only if player changed
        if info or self.lastplayer != player:
            logging.debug(f'render_display {player}: {text} ({current}/{info})')
            self.lastplayer = player
