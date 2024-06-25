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
from luma.core.interface.serial import i2c  # type: ignore
from luma.core.render import canvas  # type: ignore
from luma.oled.device import ssd1306  # type: ignore
from PIL import ImageFont

from config import config
from display import Display
from scrabble import Game, MoveType

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
SERIAL: tuple[i2c, i2c] = (
    i2c(port=IC2_PORT_PLAYER1, address=IC2_ADDRESS_PLAYER1),
    i2c(port=IC2_PORT_PLAYER2, address=IC2_ADDRESS_PLAYER2),
)
DEVICE: tuple[ssd1306, ssd1306] = (ssd1306(SERIAL[0]), ssd1306(SERIAL[1]))


def get_ipv4_address() -> dict:
    """Get IPv4 addresses for all adapters."""
    return {adapter.name: ip.ip for adapter in ifaddr.get_adapters() for ip in adapter.ips if ip.is_IPv4}


class PlayerDisplay(Display):
    """Implementation of class Display with OLED"""

    def __init__(self) -> None:
        self.game: Optional[Game] = None
        self.last_score = (0, 0)

    def stop(self) -> None:
        logging.debug('display stop')
        for i in range(2):
            DEVICE[i].hide()

    def show_boot(self) -> None:
        logging.debug('Loading message')
        ips = get_ipv4_address()
        wip: str = ips.get('wlan0', 'n/a')
        eip: str = ips.get('eth0', 'n/a')
        current_ip = (wip, eip)
        msg = 'Loading ...'
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text((1, 1), current_ip[i], font=FONT2, fill=WHITE)
                draw.text(MIDDLE, msg, font=FONT1, anchor='mm', align='center', fill=WHITE)

    def show_reset(self) -> None:
        logging.debug('New Game message')
        msg = 'New Game'
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text(MIDDLE, msg, font=FONT1, anchor='mm', align='center', fill=WHITE)

    def show_accesspoint(self) -> None:
        logging.debug('AP Mode message')
        ips = get_ipv4_address()
        wip: str = ips.get('wlan0', 'n/a')
        eip: str = ips.get('eth0', 'n/a')
        current_ip = (wip, eip)

        msg = 'AP Mode'
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text((1, 1), current_ip[i], font=FONT2, fill=WHITE)
                draw.text(MIDDLE, msg, font=FONT1, anchor='mm', align='center', fill=WHITE)

    def show_ready(self, msg=('Ready', 'Ready')) -> None:
        logging.debug('Ready message')
        ips = get_ipv4_address()
        wip: str = ips.get('wlan0', 'n/a')
        eip: str = ips.get('eth0', 'n/a')
        current_ip = (wip, eip)
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text((1, 1), current_ip[i], font=FONT2, fill=WHITE)
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
        assert player in {0, 1}, 'invalid player number'
        msg = 'Pause'
        logging.debug('Pause message')
        if config.show_score and self.game and len(self.game.moves):
            msg = f'P {self.game.moves[-1].score[player]:3d}'
        self.render_display(player, played_time, current, msg)

    def add_malus(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        assert player in {0, 1}, 'invalid player number'
        logging.debug(f'{player}: malus -10')
        self.render_display(player, played_time, current, '-10P')

    def add_remove_tiles(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        assert player in {0, 1}, 'invalid player number'
        logging.debug(f'{player}: Entf. Zug')
        self.render_display(player, played_time, current, '\u2717Zug\u270d')

    def add_doubt_timeout(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        assert player in {0, 1}, 'invalid player number'
        logging.debug(f'{player}: doubt timeout')
        self.render_display(player, played_time, current, '\u21afZeit')

    def show_cam_err(self) -> None:
        logging.debug('Cam err message')
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text(MIDDLE, '\u2620Cam', font=FONT, anchor='mm', align='center', fill=WHITE)

    def show_ftp_err(self) -> None:
        logging.debug('FTP err message')
        for i in range(2):
            with canvas(DEVICE[i]) as draw:
                draw.text(MIDDLE, '\u2620ftp', font=FONT, anchor='mm', align='center', fill=WHITE)

    def set_game(self, game: Game) -> None:
        self.game = game
        self.last_score = (0, 0)

    def _refresh_points(self, player: int, played_time: tuple[int, int], current: tuple[int, int]) -> None:
        assert player in {0, 1}, 'invalid player number'

        minutes, seconds = divmod(abs(config.max_time - played_time[player]), 60)
        text = f'-{minutes:1d}:{seconds:02d}' if config.max_time - played_time[player] < 0 else f'{minutes:02d}:{seconds:02d}'
        with canvas(DEVICE[player]) as draw:
            if config.show_score and self.game:
                nickname = self.game.nicknames[player]
                if len(nickname) > 5:
                    nickname = f'{nickname[:4]}\u2026'
                if len(self.game.moves):
                    if self.game.moves[-1].type == MoveType.UNKNOWN:
                        draw.text((20, 1), f'{nickname} ???', font=FONT2, fill=WHITE)
                    else:
                        draw.text((20, 1), f'{nickname} {self.game.moves[-1].score[player]:3d}', font=FONT2, fill=WHITE)
                else:
                    draw.text((20, 1), f'{nickname}   0', font=FONT2, fill=WHITE)
            if current[player] != 0:
                draw.text((90, 1), f'{current[player]:3d}', font=FONT1, fill=WHITE)
            draw.text((1, 22), text, font=FONT, fill=WHITE)

    def render_display(
        self, player: int, played_time: tuple[int, int], current: tuple[int, int], info: Optional[str] = None
    ) -> None:
        # pylint: disable=too-many-locals
        assert player in {0, 1}, 'invalid player number'

        # Calculate time display text
        remaining_time = config.max_time - played_time[player]
        minutes, seconds = divmod(abs(remaining_time), 60)
        time_text = f'-{minutes:1d}:{seconds:02d}' if remaining_time < 0 else f'{minutes:02d}:{seconds:02d}'

        with canvas(DEVICE[player]) as draw:
            if 0 < current[player] <= config.doubt_timeout:
                draw.text((1, 1), '\u2049', font=FONT1, fill=WHITE)  # alternative \u2718

            if info:
                left, top, right, bottom = draw.textbbox((20, 1), info, font=FONT1)
                draw.rectangle((left - 2, top - 2, right + 2, bottom + 2), fill=WHITE)
                draw.text((20, 1), info, font=FONT1, fill=BLACK)
            elif config.show_score and self.game:
                nickname = self.game.nicknames[player]
                nickname = f'{nickname[:4]}\u2026' if len(nickname) > 5 else nickname
                if self.game.moves:
                    score = self.game.moves[-1].score
                    draw.text((20, 1), f'{nickname} {score:3d}', font=FONT2, fill=WHITE)
                    if self.last_score != score:
                        self._refresh_points(0 if player == 1 else 1, played_time=played_time, current=current)
                        self.last_score = score
                else:
                    draw.text((20, 1), f'{nickname}   0', font=FONT2, fill=WHITE)
            elif self.game:
                nickname = self.game.nicknames[player][:10]
                draw.text((20, 1), f'{nickname}', font=FONT2, fill=WHITE)
            if current[player] != 0:
                draw.text((90, 1), f'{current[player]:3d}', font=FONT1, fill=WHITE)

            draw.text((1, 22), time_text, font=FONT, fill=WHITE)
