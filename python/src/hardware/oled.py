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
import atexit
import logging
import time
from typing import Optional

import adafruit_ssd1306  # type: ignore
import board  # type: ignore
from PIL import Image, ImageDraw, ImageFont
from smbus import SMBus  # type: ignore

from config import config
from display import Display
from util import Singleton


class PlayerDisplay(Display, metaclass=Singleton):
    """Implementation of class Display with OLED"""

    def __init__(self):
        self.i2cbus = SMBus(1)
        self.i2c = board.I2C()
        self.i2cbus.write_byte(0x70, 1 << 1)  # display 1
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c, addr=0x3C)
        self.oled.init_display()
        self.i2cbus.write_byte(0x70, 1 << 0)  # display 0
        self.oled.init_display()
        self.font_family = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
        self.font = ImageFont.truetype(self.font_family, 42)
        self.font1 = ImageFont.truetype(self.font_family, 20)
        self.empty = Image.new('1', (self.oled.width, self.oled.height))
        self.image = [Image.new('1', (self.oled.width, self.oled.height)),
                      Image.new('1', (self.oled.width, self.oled.height))]
        self.draw = [ImageDraw.Draw(self.image[0]), ImageDraw.Draw(self.image[1])]
        atexit.register(self.stop)

    def stop(self) -> None:
        logging.debug('display stop')
        for i in range(2):
            self.display(i)
            self.oled.poweroff()

    def display(self, disp: int) -> None:
        """active display on multiplexer"""
        assert disp in [0, 1], "invalid display"
        self.i2cbus.write_byte(0x70, 1 << disp)
        time.sleep(0.001)

    def show_boot(self) -> None:
        logging.debug('Boot message')
        msg = 'Boot'
        width = self.font.getlength(msg)
        coord = (self.oled.width // 2 - width // 2, 20)
        for i in range(2):
            self.image[i].paste(self.empty)
            self.draw[i].text(coord, msg, font=self.font, fill=255)
        self.show()

    def show_reset(self) -> None:
        logging.debug('Reset message')
        msg = 'Reset'
        width = self.font.getlength(msg)
        coord = (self.oled.width // 2 - width // 2, 20)
        for i in range(2):
            self.image[i].paste(self.empty)
            self.draw[i].text(coord, msg, font=self.font, fill=255)
        self.show(invert=False)

    def show_ready(self) -> None:
        logging.debug('Ready message')
        minutes, seconds = divmod(abs(config.max_time), 60)
        for i in range(2):
            self.image[i].paste(self.empty)
            self.draw[i].text((1, 22), f'{minutes:02d}:{seconds:02d}', font=self.font, fill=255)
        self.show(invert=False)

    def show_pause(self, player: int) -> None:
        assert player in [0, 1], "invalid player number"
        logging.debug('Pause message')
        msg = 'Pause'
        coord = (24, 1)
        self.draw[player].rectangle((24, 0, self.oled.width, 24), fill=0)
        self.draw[player].text(coord, msg, font=self.font1, fill=255)
        self.show(player=player, invert=True)

    def add_malus(self, player: int) -> None:
        assert player in [0, 1], "invalid player number"

        logging.debug(f'{player}: malus -10')
        msg = '-10P'
        coord = (24, 1)
        self.draw[player].rectangle((24, 0, self.oled.width, 24), fill=0)
        self.draw[player].text(coord, msg, font=self.font1, fill=255)
        self.show(player=player)

    def add_remove_tiles(self, player: int) -> None:
        assert player in [0, 1], "invalid player number"

        logging.debug(f'{player}: Entf. Zug')
        msg = '\u2717Zug\u270D'
        coord = (24, 1)
        self.draw[player].rectangle((24, 0, self.oled.width, 24), fill=0)
        self.draw[player].text(coord, msg, font=self.font1, fill=255)
        self.show(player=player)

    def add_doubt_timeout(self, player: int) -> None:
        assert player in [0, 1], "invalid player number"

        logging.debug(f'{player}: doubt timeout')
        msg = '\u21AFtimeout'
        coord = (24, 1)
        self.draw[player].rectangle((24, 0, self.oled.width, 24), fill=0)
        self.draw[player].text(coord, msg, font=self.font1, fill=255)
        self.show(player=player)

    def show_cam_err(self) -> None:
        logging.debug('Cam err message')
        msg = '\u2620Cam'
        coord = (1, 16)
        for i in range(2):
            self.image[i].paste(self.empty)
            self.draw[i].text(coord, msg, font=self.font, fill=255)
        self.show()

    def show_ftp_err(self) -> None:
        logging.debug('FTP err message')
        msg = '\u2620ftp'
        coord = (1, 16)
        for i in range(2):
            self.image[i].paste(self.empty)
            self.draw[i].text(coord, msg, font=self.font, fill=255)
        self.show()

    def show_config(self) -> None:
        logging.debug('Cfg message')
        msg = '\u270ECfg'
        coord = (1, 16)
        for i in range(0, 2):
            self.image[i].paste(self.empty)
            self.draw[i].text(coord, msg, font=self.font, fill=255)
        self.show()

    def add_time(self, player, time1, played1, time2, played2) -> None:
        msg = '\u2049'  # \u2718
        coord = (1, 0)

        self.image[player].paste(self.empty)
        text = ''
        played_time = 0
        if player == 0:
            # display 0
            minutes1, seconds1 = divmod(abs(config.max_time - time1), 60)
            text = f'-{minutes1:1d}:{seconds1:02d}' if config.max_time - time1 < 0 else f'{minutes1:02d}:{seconds1:02d}'
            played_time = played1
        elif player == 1:
            # display 1
            minutest2, seconds2 = divmod(abs(config.max_time - time2), 60)
            text = f'-{minutest2:1d}:{seconds2:02d}' if config.max_time - time2 < 0 else f'{minutest2:02d}:{seconds2:02d}'
            played_time = played2

        self.draw[player].text((1, 22), text, font=self.font, fill=255)
        self.draw[player].text((80, 1), f'{played_time:4d}', font=self.font1, fill=255)
        if played_time <= config.doubt_timeout:
            self.draw[player].text(coord, msg, font=self.font1, fill=255)
        self.display(player)
        self.oled.image(self.image[player])
        self.oled.show()

    def clear(self):
        for i in range(2):
            self.display(i)
            self.oled.fill(0)
        # self.oled.show()

    def clear_message(self, player: Optional[int] = None) -> None:
        if player is None:
            for i in range(2):
                self.draw[i].rectangle((0, 0, self.oled.width, 24), fill=0)
            self.show()
        else:
            assert player in [0, 1], "invalid display"
            self.draw[player].rectangle((0, 0, self.oled.width, 24), fill=0)
            self.show(player=player)

    def show(self, player: Optional[int] = None, invert: Optional[bool] = None) -> None:
        if player is None:
            for i in range(2):
                self.display(i)
                if invert is not None:
                    self.oled.invert(invert)
                self.oled.image(self.image[i])
                self.oled.show()
        else:
            assert player in [0, 1], "invalid display"
            self.display(player)
            if invert is not None:
                self.oled.invert(invert)
            self.oled.image(self.image[player])
            self.oled.show()
