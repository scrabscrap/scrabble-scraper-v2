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

import ifaddr
from luma.core.error import DeviceNotFoundError
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

from config import config
from display import Display
from scrabble import Game

IC2_PORT_PLAYER1 = 1
IC2_ADDRESS_PLAYER1 = 0x3C
IC2_PORT_PLAYER2 = 3
IC2_ADDRESS_PLAYER2 = 0x3C
BLACK = 'black'
WHITE = 'white'
MIDDLE = (64, 42)

# docu https://luma-oled.readthedocs.io/en/latest/index.html

FONT_FAMILY = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
FONT = ImageFont.truetype(FONT_FAMILY, 42)
FONT1 = ImageFont.truetype(FONT_FAMILY, 20)
FONT2 = ImageFont.truetype(FONT_FAMILY, 12)
try:
    SERIAL: tuple[i2c, i2c] = (
        i2c(port=IC2_PORT_PLAYER1, address=IC2_ADDRESS_PLAYER1),
        i2c(port=IC2_PORT_PLAYER2, address=IC2_ADDRESS_PLAYER2),
    )
    DEVICE: tuple[ssd1306, ssd1306] = (ssd1306(SERIAL[0]), ssd1306(SERIAL[1]))
except (OSError, DeviceNotFoundError) as e:
    logging.basicConfig(filename=f'{config.work_dir}/log/messages.log', level=logging.INFO, force=True)
    logging.error(f'error opening OLED 1 / OLED 2 {type(e).__name__}: {e}')
    raise RuntimeError('Error: OLED 1 / OLED 2 not available') from e


def get_ipv4_address() -> dict:
    """Get IPv4 addresses for all adapters."""
    return {adapter.name: ip.ip for adapter in ifaddr.get_adapters() for ip in adapter.ips if ip.is_IPv4}


class PlayerDisplay(Display):
    """Implementation of class Display with OLED"""

    def __init__(self) -> None:
        self.game: Optional[Game] = None

    def stop(self) -> None:
        logging.debug('display stop')
        for i in range(2):
            DEVICE[i].hide()

    def show_boot(self) -> None:
        self.show_ready(('Loading\u2026', 'Loading\u2026'))

    def show_accesspoint(self) -> None:
        self.show_ready(('AP Mode', 'AP Mode'))

    def show_ready(self, msg=('Ready', 'Ready')) -> None:
        logging.debug(f'show message {msg}')
        ips = get_ipv4_address()
        wip: str = ips.get('wlan0', 'n/a')
        eip: str = ips.get('eth0', 'n/a')
        title = (wip, eip)
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text((1, 1), title[i], font=FONT2, fill=WHITE)
                text = msg[i][:10]
                draw.text(MIDDLE, text, font=FONT1, anchor='mm', align='center', fill=WHITE)

    def show_end_of_game(self) -> None:
        if self.game:
            for i in range(2):
                with canvas(DEVICE[i]) as draw:
                    nickname = self.game.nicknames[i][:10]
                    draw.text((2, 5), f'{nickname}', font=FONT1, fill=WHITE)
                    if self.game.moves:
                        minutes, seconds = divmod(abs(config.max_time - self.game.moves[-1].played_time[i]), 60)
                        score = self.game.moves[-1].score[i]
                        draw.text((2, 30), f'{minutes:02d}:{seconds:02d}  {score:3d}', font=FONT1, fill=WHITE)

    def show_pause(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        msg = 'Pause'
        logging.debug('Pause message')
        if config.show_score and self.game and len(self.game.moves):
            msg = f'P {self.game.moves[-1].score[player]:3d}'
        self.render_display(player, played_time, current, msg)

    def add_malus(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        logging.debug(f'{player}: malus -10')
        self.render_display(player, played_time, current, '-10P')

    def add_remove_tiles(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        logging.debug(f'{player}: Entf. Zug')
        self.render_display(player, played_time, current, '\u2717Zug\u270d')

    def add_doubt_timeout(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        logging.debug(f'{player}: doubt timeout')
        self.render_display(player, played_time, current, '\u21afZeit')

    def show_cam_err(self) -> None:
        self.show_ready(('\u2620 Cam err', '\u2620 Cam err'))

    def show_ftp_err(self) -> None:
        self.show_ready(('\u2620 FTP err', '\u2620 FTP err'))

    def set_game(self, game: Game) -> None:
        self.game = game

    def render_display(
        self, player: int, played_time: tuple[int, int], current: tuple[int, int], info: Optional[str] = None
    ) -> None:
        def _format_time(played: int) -> str:
            delta = config.max_time - played
            minutes, seconds = divmod(abs(delta), 60)
            return f'-{minutes:1d}:{seconds:02d}' if delta < 0 else f'{minutes:02d}:{seconds:02d}'

        def _shorten_nickname(nickname: str, max_length: int = 6) -> str:
            return f'{nickname[: max_length - 1]}\u2026' if len(nickname) > max_length else nickname

        for i in range(2):
            time_str = _format_time(played_time[i])
            color = WHITE
            with canvas(DEVICE[i]) as draw:
                if info and i == player:
                    draw.rectangle((1, 1, 128, 64), fill=WHITE)  # white background
                    color = BLACK
                if info:
                    draw.text((20, 1), info, font=FONT1, fill=color)
                if i == player:
                    if 0 < current[player] <= config.doubt_timeout:
                        draw.text((1, 1), '\u2049', font=FONT1, fill=color)  # alternative \u2718
                    if current[player] != 0:
                        draw.text((90, 1), f'{current[player]:3d}', font=FONT1, fill=color)
                if self.game and not info:
                    if config.show_score:
                        nickname = _shorten_nickname(self.game.nicknames[player])
                        score = self.game.moves[-1].score[i] if len(self.game.moves) else 0
                        draw.text((20, 1), f'{nickname}{score:3d}', font=FONT2, fill=color)
                    else:
                        nickname = _shorten_nickname(self.game.nicknames[i], 10)
                        draw.text((20, 1), f'{nickname}', font=FONT2, fill=color)
                draw.text((1, 22), time_str, font=FONT, fill=color)
