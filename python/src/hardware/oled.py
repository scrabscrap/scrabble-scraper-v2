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

from config import config
from display import Display
from util import Singleton

IC2_PORT_PLAYER1 = 1
IC2_ADDRESS_PLAYER1 = 0x3c
IC2_PORT_PLAYER2 = 3
IC2_ADDRESS_PLAYER2 = 0x3c
BLACK = 'black'
WHITE = 'white'

# docu https://luma-oled.readthedocs.io/en/latest/index.html


class PlayerDisplay(Display, metaclass=Singleton):
    """Implementation of class Display with OLED"""

    def __init__(self):
        self.font_family = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
        self.font = ImageFont.truetype(self.font_family, 42)
        self.font1 = ImageFont.truetype(self.font_family, 20)
        self.font2 = ImageFont.truetype(self.font_family, 12)
        self.serial: tuple[i2c, i2c] = (
            i2c(port=IC2_PORT_PLAYER1, address=IC2_ADDRESS_PLAYER1),
            i2c(port=IC2_PORT_PLAYER2, address=IC2_ADDRESS_PLAYER2))
        self.device: tuple[ssd1306, ssd1306] = (
            ssd1306(self.serial[0]), ssd1306(self.serial[1]))

    def stop(self) -> None:
        logging.debug('display stop')
        for i in range(2):
            self.device[i].hide()

    def show_boot(self, current_ip=('', '')) -> None:
        logging.debug('Boot message')
        try:
            wip: str = netifaces.ifaddresses('wlan0')[netifaces.AF_INET][0]['addr']  # pylint: disable=I1101
        except KeyError:
            wip = 'n/a'
        try:
            eip: str = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']  # pylint: disable=I1101
        except KeyError:
            eip = 'n/a'
        current_ip = (wip, eip)
        msg = 'Boot'
        width = self.font.getlength(msg)
        coord = (self.device[0].width // 2 - width // 2, 20)
        for i in range(2):
            with canvas(self.device[i]) as draw:
                draw.text((12, 0), current_ip[i], font=self.font2, fill=WHITE)
                draw.text(coord, msg, font=self.font, fill=WHITE)

    def show_reset(self) -> None:
        logging.debug('Reset message')
        with canvas(self.device[0]) as draw:
            msg = 'New'
            width = self.font.getlength(msg)
            coord = (self.device[0].width // 2 - width // 2, 20)
            draw.text(coord, msg, font=self.font, fill=WHITE)
        with canvas(self.device[1]) as draw:
            msg = 'Game'
            width = self.font.getlength(msg)
            coord = (self.device[1].width // 2 - width // 2, 20)
            draw.text(coord, msg, font=self.font, fill=WHITE)

    def show_accesspoint(self) -> None:
        logging.debug('AP Mode message')
        msg = 'AP Mode'
        width = self.font1.getlength(msg)
        for i in range(2):
            coord = (self.device[i].width // 2 - width // 2, 20)
            with canvas(self.device[i]) as draw:
                draw.text(coord, msg, font=self.font1, fill=WHITE)

    def show_ready(self, msg=('Ready', 'Ready')) -> None:
        logging.debug('Ready message')
        for i in range(2):
            with canvas(self.device[i]) as draw:
                text = msg[i][:10]
                width = self.font1.getlength(text)
                coord = (self.device[i].width // 2 - width // 2, 20)
                draw.text(coord, text, font=self.font1, fill=WHITE)

    def show_pause(self, player: int, played_time: list[int], current: list[int]) -> None:
        assert player in [0, 1], "invalid player number"
        logging.debug('Pause message')
        self.render_display(player, played_time, current, 'Pause')

    def add_malus(self, player: int, played_time: list[int], current: list[int]) -> None:
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: malus -10')
        self.render_display(player, played_time, current, '-10P')

    def add_remove_tiles(self, player: int, played_time: list[int], current: list[int]) -> None:
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: Entf. Zug')
        self.render_display(player, played_time, current, '\u2717Zug\u270D')

    def add_doubt_timeout(self, player: int, played_time: list[int], current: list[int]) -> None:
        assert player in [0, 1], "invalid player number"
        logging.debug(f'{player}: doubt timeout')
        self.render_display(player, played_time, current, '\u21AFZeit')

    def show_cam_err(self) -> None:
        logging.debug('Cam err message')
        for i in range(2):
            with canvas(self.device[i]) as draw:
                draw.text((1, 16), '\u2620Cam', font=self.font, fill=WHITE)

    def show_ftp_err(self) -> None:
        logging.debug('FTP err message')
        for i in range(2):
            with canvas(self.device[i]) as draw:
                draw.text((1, 16), '\u2620ftp', font=self.font, fill=WHITE)

    def show_config(self) -> None:
        logging.debug('Cfg message')
        for i in range(2):
            with canvas(self.device[i]) as draw:
                draw.text((1, 16), '\u270ECfg', font=self.font, fill=WHITE)

    def render_display(self, player: int, played_time: list[int], current: list[int], info: Optional[str] = None) -> None:
        assert player in [0, 1], "invalid player number"

        minutes, seconds = divmod(abs(config.max_time - played_time[player]), 60)
        text = f'-{minutes:1d}:{seconds:02d}' if config.max_time - played_time[player] < 0 else f'{minutes:02d}:{seconds:02d}'
        with canvas(self.device[player]) as draw:
            if current[player] <= config.doubt_timeout:
                draw.text((0, 1), '\u2049', font=self.font1, fill=WHITE)  # alternative \u2718
            if info:
                draw.text((24, 1), info, font=self.font1, fill=WHITE)
            draw.text((80, 1), f'{current[player]:4d}', font=self.font1, fill=WHITE)
            draw.text((1, 22), text, font=self.font, fill=WHITE)
