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

import netifaces  # type: ignore
from luma.core.interface.serial import i2c  # type: ignore
from luma.core.render import canvas  # type: ignore
from luma.oled.device import ssd1306  # type: ignore
from PIL import ImageFont

from config import Config
from display import Display
from scrabble import Game, MoveType

IC2_PORT_PLAYER1 = 1
IC2_ADDRESS_PLAYER1 = 0x3c
IC2_PORT_PLAYER2 = 3
IC2_ADDRESS_PLAYER2 = 0x3c
BLACK = 'black'
WHITE = 'white'
MIDDLE = (64, 42)

# docu https://luma-oled.readthedocs.io/en/latest/index.html

FONT_FAMILY = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
FONT = ImageFont.truetype(FONT_FAMILY, 44)
FONT1 = ImageFont.truetype(FONT_FAMILY, 20)
FONT2 = ImageFont.truetype(FONT_FAMILY, 12)
SERIAL: tuple[i2c, i2c] = (
    i2c(port=IC2_PORT_PLAYER1, address=IC2_ADDRESS_PLAYER1),
    i2c(port=IC2_PORT_PLAYER2, address=IC2_ADDRESS_PLAYER2))
DEVICE: tuple[ssd1306, ssd1306] = (
    ssd1306(SERIAL[0]), ssd1306(SERIAL[1]))


class PlayerDisplay(Display):
    # pylint: disable=too-many-instance-attributes
    """Implementation of class Display with OLED"""
    game: Optional[Game] = None
    last_score = (0, 0)

    @classmethod
    def stop(cls) -> None:
        logging.debug('display stop')
        for i in range(2):
            DEVICE[i].hide()

    @classmethod
    def show_boot(cls) -> None:
        logging.debug('Loading message')
        try:
            wip: str = netifaces.ifaddresses('wlan0')[netifaces.AF_INET][0]['addr']  # pylint: disable=c-extension-no-member
        except KeyError:
            wip = 'n/a'
        try:
            eip: str = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']  # pylint: disable=c-extension-no-member
        except KeyError:
            eip = 'n/a'
        current_ip = (wip, eip)
        msg = 'Loading ...'
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text((1, 1), current_ip[i], font=FONT2, fill=WHITE)
                draw.text(MIDDLE, msg, font=FONT1, anchor='mm', align='center', fill=WHITE)

    @classmethod
    def show_reset(cls) -> None:
        logging.debug('New Game message')
        msg = 'New Game'
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text(MIDDLE, msg, font=FONT1, anchor='mm', align='center', fill=WHITE)

    @classmethod
    def show_accesspoint(cls) -> None:
        logging.debug('AP Mode message')
        try:
            wip: str = netifaces.ifaddresses('wlan0')[netifaces.AF_INET][0]['addr']  # pylint: disable=c-extension-no-member
        except KeyError:
            wip = 'n/a'
        try:
            eip: str = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']  # pylint: disable=c-extension-no-member
        except KeyError:
            eip = 'n/a'
        current_ip = (wip, eip)

        msg = 'AP Mode'
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text((1, 1), current_ip[i], font=FONT2, fill=WHITE)
                draw.text(MIDDLE, msg, font=FONT1, anchor='mm', align='center', fill=WHITE)

    @classmethod
    def show_ready(cls, msg=('Ready', 'Ready')) -> None:
        logging.debug('Ready message')
        try:
            wip: str = netifaces.ifaddresses('wlan0')[netifaces.AF_INET][0]['addr']  # pylint: disable=c-extension-no-member
        except KeyError:
            wip = 'n/a'
        try:
            eip: str = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']  # pylint: disable=c-extension-no-member
        except KeyError:
            eip = 'n/a'
        current_ip = (wip, eip)
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text((1, 1), current_ip[i], font=FONT2, fill=WHITE)
                text = msg[i][:10]
                draw.text(MIDDLE, text, font=FONT1, anchor='mm', align='center', fill=WHITE)

    @classmethod
    def show_end_of_game(cls) -> None:
        if cls.game:
            for i in range(0, 2):
                with canvas(DEVICE[i]) as draw:
                    nickname = cls.game.nicknames[i][:10]
                    draw.text((2, 5), f'{nickname}', font=FONT1, fill=WHITE)
                    minutes, seconds = divmod(abs(Config.max_time() - cls.game.moves[-1].played_time[i]), 60)
                    score = cls.game.moves[-1].score[i]
                    draw.text((2, 30), f'{minutes:02d}:{seconds:02d}  {score:3d}', font=FONT1, fill=WHITE)

    @classmethod
    def show_pause(cls, player: int, played_time: list[int], current: list[int]) -> None:
        assert player in [0, 1], "invalid player number"
        msg = 'Pause'
        logging.debug('Pause message')
        if Config.show_score() and cls.game:
            if len(cls.game.moves):
                msg = f'P {cls.game.moves[-1].score[player]:3d}'
        cls.render_display(player, played_time, current, msg)

    @classmethod
    def add_malus(cls, player: int, played_time: list[int], current: list[int]) -> None:
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: malus -10')
        cls.render_display(player, played_time, current, '-10P')

    @classmethod
    def add_remove_tiles(cls, player: int, played_time: list[int], current: list[int]) -> None:
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: Entf. Zug')
        cls.render_display(player, played_time, current, '\u2717Zug\u270D')

    @classmethod
    def add_doubt_timeout(cls, player: int, played_time: list[int], current: list[int]) -> None:
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: doubt timeout')
        cls.render_display(player, played_time, current, '\u21AFZeit')

    @classmethod
    def show_cam_err(cls) -> None:
        logging.debug('Cam err message')
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text(MIDDLE, '\u2620Cam', font=FONT, anchor='mm', align='center', fill=WHITE)

    @classmethod
    def show_ftp_err(cls) -> None:
        logging.debug('FTP err message')
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text(MIDDLE, '\u2620ftp', font=FONT, anchor='mm', align='center', fill=WHITE)

    @classmethod
    def set_game(cls, game: Game) -> None:
        cls.game = game
        cls.last_score = (0, 0)

    @classmethod
    def _refresh_points(cls, player: int, played_time: list[int], current: list[int]) -> None:
        assert player in [0, 1], "invalid player number"

        minutes, seconds = divmod(abs(Config.max_time() - played_time[player]), 60)
        text = f'-{minutes:1d}:{seconds:02d}' if Config.max_time() - played_time[player] < 0 else f'{minutes:02d}:{seconds:02d}'
        with canvas(DEVICE[player]) as draw:
            if Config.show_score() and cls.game:
                nickname = cls.game.nicknames[player]
                if len(nickname) > 5:
                    nickname = f'{nickname[:4]}\u2026'
                if len(cls.game.moves):
                    if cls.game.moves[-1].type == MoveType.UNKNOWN:
                        draw.text((20, 1), f'{nickname} ???', font=FONT2, fill=WHITE)
                    else:
                        draw.text((20, 1), f'{nickname} {cls.game.moves[-1].score[player]:3d}', font=FONT2, fill=WHITE)
                else:
                    draw.text((20, 1), f'{nickname}   0', font=FONT2, fill=WHITE)
            if current[player] != 0:
                draw.text((90, 1), f'{current[player]:3d}', font=FONT1, fill=WHITE)
            draw.text((1, 22), text, font=FONT, fill=WHITE)

    @classmethod
    def render_display(cls, player: int, played_time: list[int], current: list[int], info: Optional[str] = None) -> None:
        assert player in [0, 1], "invalid player number"

        minutes, seconds = divmod(abs(Config.max_time() - played_time[player]), 60)
        text = f'-{minutes:1d}:{seconds:02d}' if Config.max_time() - played_time[player] < 0 else f'{minutes:02d}:{seconds:02d}'
        with canvas(DEVICE[player]) as draw:
            if 0 < current[player] <= Config.doubt_timeout():
                draw.text((1, 1), '\u2049', font=FONT1, fill=WHITE)  # alternative \u2718
            if info:
                left, top, right, bottom = draw.textbbox((20, 1), info, font=FONT1)
                draw.rectangle((left - 2, top - 2, right + 2, bottom + 2), fill=WHITE)
                draw.text((20, 1), info, font=FONT1, fill=BLACK)
            elif Config.show_score() and cls.game:
                nickname = cls.game.nicknames[player]
                if len(nickname) > 5:
                    nickname = f'{nickname[:4]}\u2026'
                if len(cls.game.moves):
                    draw.text((20, 1), f'{nickname} {cls.game.moves[-1].score[player]:3d}', font=FONT2, fill=WHITE)
                    if cls.last_score != cls.game.moves[-1].score:
                        cls._refresh_points(0 if player == 1 else 1, played_time=played_time, current=current)
                        cls.last_score = cls.game.moves[-1].score
                else:
                    draw.text((20, 1), f'{nickname}   0', font=FONT2, fill=WHITE)
            elif cls.game:
                nickname = cls.game.nicknames[player][:10]
                draw.text((20, 1), f'{nickname}', font=FONT2, fill=WHITE)
            if current[player] != 0:
                draw.text((90, 1), f'{current[player]:3d}', font=FONT1, fill=WHITE)

            draw.text((1, 22), text, font=FONT, fill=WHITE)
