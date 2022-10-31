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
from config import config
from display import Display
from PIL import Image, ImageDraw, ImageFont
from smbus import SMBus  # type: ignore
from util import Singleton


class PlayerDisplay(Display, metaclass=Singleton):
    """Implementation of class Display with OLED"""

    def __init__(self):
        self.TCA9548A_select(0)
        i2c = board.I2C()
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
        self.oled.init_display()
        self.TCA9548A_select(1)
        self.oled.init_display()
        self.font_family = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
        self.font = ImageFont.truetype(self.font_family, 42)
        self.font1 = ImageFont.truetype(self.font_family, 20)
        self.empty = Image.new('1', (self.oled.width, self.oled.height))
        self.image = [Image.new('1', (self.oled.width, self.oled.height)),
                      Image.new('1', (self.oled.width, self.oled.height))]
        self.draw = [ImageDraw.Draw(self.image[0]), ImageDraw.Draw(self.image[1])]
        atexit.register(self.stop)

    def TCA9548A_select(self, channel: int) -> None:
        """select channel on multiplexer"""
        assert channel in [0, 1], "invalid channel number"
        channel_array = [0b00000001, 0b00000010]
        bus = SMBus(1)
        bus.write_byte(0x70, channel_array[channel])
        time.sleep(0.01)

    def stop(self) -> None:
        logging.debug('display stop')
        for i in range(2):
            self.TCA9548A_select(i)
            self.oled.poweroff()

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

    def show_ready(self, msg=('Ready', 'Ready')) -> None:
        logging.debug('Ready message')
        minutes, seconds = divmod(abs(config.max_time), 60)
        for i in range(2):
            self.image[i].paste(self.empty)
            text = msg[i][:10]
            width = self.font1.getlength(text)
            coord = (self.oled.width // 2 - width // 2, 20)
            self.draw[i].text(coord, text, font=self.font1, fill=255)
            self.show(i, invert=False)  # show "Ready"
            self.image[i].paste(self.empty)  # prepare start timer
            self.draw[i].text((1, 22), f'{minutes:02d}:{seconds:02d}', font=self.font, fill=255)

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
        for i in range(2):
            self.image[i].paste(self.empty)
            self.draw[i].text(coord, msg, font=self.font, fill=255)
        self.show()

    def add_time(self, player, time1, played1, time2, played2) -> None:
        assert player in [0, 1], "invalid player number"

        time = time1 if player == 0 else time2
        played_time = played1 if player == 0 else played2
        minutes, seconds = divmod(abs(config.max_time - time), 60)
        text = f'-{minutes:1d}:{seconds:02d}' if config.max_time - time < 0 else f'{minutes:02d}:{seconds:02d}'
        self.image[player].paste(self.empty)
        self.draw[player].text((1, 22), text, font=self.font, fill=255)
        self.draw[player].text((80, 1), f'{played_time:4d}', font=self.font1, fill=255)
        if played_time <= config.doubt_timeout:
            msg = '\u2049'  # \u2718
            self.draw[player].text((1, 0), msg, font=self.font1, fill=255)
        self.show(player=player)

    def clear(self):
        for i in range(2):
            self.image[i].paste(self.empty)
        self.show(invert=False)

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
                self.TCA9548A_select(i)
                if invert is not None:
                    self.oled.invert(invert)
                self.oled.image(self.image[i])
                self.oled.show()
        else:
            assert player in [0, 1], "invalid display"
            self.TCA9548A_select(player)
            if invert is not None:
                self.oled.invert(invert)
            self.oled.image(self.image[player])
            self.oled.show()
