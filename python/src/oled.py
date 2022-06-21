"""
 This file is part of the scrabble-scraper distribution (https://github.com/scrabscrap/scrabble-scraper)
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

import adafruit_ssd1306
import board
from PIL import Image, ImageDraw, ImageFont
import time

from smbus import SMBus
from config import config
from display import Display

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(module)s - %(levelname)s - %(message)s')


class OledDisplay(Display):

    def __init__(self):
        # todo: 2nd display
        self.i2cbus = SMBus(1)
        self.i2c = board.I2C()
        # init both displays
        self.i2cbus.write_byte(0x70, 1 << 1)
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c, addr=0x3C)
        self.oled.init_display()
        self.i2cbus.write_byte(0x70, 1 << 0)
        self.oled.init_display()
        self.font_family = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
        self.font = ImageFont.truetype(self.font_family, 42)
        self.font1 = ImageFont.truetype(self.font_family, 20)
        self.empty = Image.new('1', (self.oled.width, self.oled.height))
        self.image = [Image.new('1', (self.oled.width, self.oled.height)),
                      Image.new('1', (self.oled.width, self.oled.height))]
        self.draw = [ImageDraw.Draw(self.image[0]),
                     ImageDraw.Draw(self.image[1])]

    def stop(self) -> None:
        self.display(0)
        self.oled.poweroff()
        self.display(1)
        self.oled.poweroff()

    def display(self, number: int) -> None:
        self.i2cbus.write_byte(0x70, 1 << number)
        time.sleep(0.001)

    def show_boot(self) -> None:
        MSG_BOOT = 'Boot'
        MSG_BOOT_FONT = self.font
        (msg_boot_width, _) = MSG_BOOT_FONT.getsize(MSG_BOOT)
        MSG_BOOT_COORD = (self.oled.width // 2 - msg_boot_width // 2, 20)
        logging.debug('Boot message')
        for i in range(0, 2):
            self.image[i].paste(self.empty)
            self.draw[i].text(MSG_BOOT_COORD, MSG_BOOT,
                              font=MSG_BOOT_FONT, fill=255)
            self.display(i)
            self.oled.image(self.image[i])
            self.oled.show()

    def show_reset(self) -> None:
        MSG_RESET = 'Reset'
        MSG_RESET_FONT = self.font
        (msg_boot_width, _) = MSG_RESET_FONT.getsize(MSG_RESET)
        MSG_RESET_COORD = (self.oled.width // 2 - msg_boot_width // 2, 20)
        logging.debug('Reset message')
        for i in range(0,2):
            self.image[i].paste(self.empty)
            self.draw[i].text(MSG_RESET_COORD, MSG_RESET,
                        font=MSG_RESET_FONT, fill=255)
            self.display(i)
            self.oled.image(self.image[i])
            self.oled.show()

    def show_ready(self) -> None:
        logging.debug('Ready message')
        m1, s1 = divmod(abs(config.MAX_TIME), 60)
        for i in range (0,2):
            self.image[i].paste(self.empty)
            self.draw[i].text((1, 22), f'{m1:02d}:{s1:02d}', font=self.font, fill=255)
            self.display(i)
            self.oled.image(self.image[i])
            self.oled.show()

    def show_pause(self, player) -> None:
        MSG_BREAK = 'Pause'
        MSG_BREAK_FONT = self.font1
        MSG_BREAK_COORD = (24, 1)
        self.draw[player].text(MSG_BREAK_COORD, MSG_BREAK,
                    font=MSG_BREAK_FONT, fill=255)
        self.display(player)
        self.oled.image(self.image[player])
        self.oled.show()

    def add_malus(self, player) -> None:
        MSG_MALUS = '-10P'
        MSG_MALUS_FONT = self.font1
        # (msg_malus_width, _) = MSG_MALUS_FONT.getsize(MSG_MALUS)
        MSG_MALUS_COORD = (24, 1)
        (w, h) = MSG_MALUS_FONT.getsize(MSG_MALUS)
        logging.debug('(0) malus -10')
        self.draw[player].rectangle((24, 0, self.oled.width, 24), fill=0)
        self.draw[player].text(MSG_MALUS_COORD, MSG_MALUS,
                        font=MSG_MALUS_FONT, fill=255)
        self.display(player)
        self.oled.image(self.image[player])
        self.oled.show()

    def add_remove_tiles(self, player) -> None:
        MSG_REMOVE_TILES = '\u2717Zug\u270D'
        MSG_REMOVE_TILES_FONT = self.font1
        # (msg_remove_width, _) = MSG_REMOVE_TILES_FONT.getsize(MSG_REMOVE_TILES)
        MSG_REMOVE_TILES_COORD = (24, 1)
        (w, h) = MSG_REMOVE_TILES_FONT.getsize(MSG_REMOVE_TILES)
        logging.debug(f'size: w{w:d}/h{h:d}')

        logging.debug('(0) Entf. Zug')
        self.draw[player].rectangle((24, 0, self.oled.width, 24), fill=0)
        self.draw[player].text(MSG_REMOVE_TILES_COORD, MSG_REMOVE_TILES,
                        font=MSG_REMOVE_TILES_FONT, fill=255)
        self.display(player)
        self.oled.image(self.image[player])
        self.oled.show()

    def show_cam_err(self) -> None:
        MSG_ERR_CAM = '\u2620Cam'
        MSG_ERR_CAM_FONT = self.font
        MSG_ERR_CAM_COORD = (1, 16)
        logging.debug('Cam Err')
        for i in range(0,2):
            self.draw[i].text(MSG_ERR_CAM_COORD, MSG_ERR_CAM,
                        font=MSG_ERR_CAM_FONT, fill=255)
            self.display(i)
            self.oled.image(self.image[i])
            self.oled.show()

    def show_ftp_err(self) -> None:
        MSG_ERR_FTP = '\u2620ftp'
        MSG_ERR_FTP_FONT = self.font
        MSG_ERR_FTP_COORD = (1, 16)
        logging.debug('FTP Err')
        for i in range (0,2):
            self.draw[i].text(MSG_ERR_FTP_COORD, MSG_ERR_FTP,
                        font=MSG_ERR_FTP_FONT, fill=255)
            self.display(i)
            self.oled.image(self.image[i])
            self.oled.show()

    def show_config(self) -> None:
        MSG_CONFIG = '\u270ECfg'
        MSG_CONFIG_FONT = self.font
        MSG_CONFIG_COORD = (1, 16)
        logging.debug('Cfg')
        for i in range (0,2):
            self.draw[i].text(MSG_CONFIG_COORD, MSG_CONFIG,
                        font=MSG_CONFIG_FONT, fill=255)
            self.display(i)
            self.oled.image(self.image[i])
            self.oled.show()

    def add_time(self, player, t1, p1, t2, p2) -> None:
        MSG_DOUBT = '\u2049'  # \u2718
        MSG_DOUBT_FONT = self.font1
        (msg_doubt_width, _) = MSG_DOUBT_FONT.getsize(MSG_DOUBT)
        MSG_DOUBT_COORD = (1, 0)

        self.image[player].paste(self.empty)
        text = ''
        p = 0
        if player == 0:
            # display 0
            m1, s1 = divmod(abs(config.MAX_TIME - t1), 60)
            text = f'-{m1:1d}:{s1:02d}' if config.MAX_TIME - \
                t1 < 0 else f'{m1:02d}:{s1:02d}'
            p = p1
        elif player == 1:
            # display 1
            m2, s2 = divmod(abs(config.MAX_TIME - t2), 60)
            text = f'-{m2:1d}:{s2:02d}' if config.MAX_TIME - \
                t2 < 0 else f'{m2:02d}:{s2:02d}'
            p = p2

        self.draw[player].text((1, 22), text, font=self.font, fill=255)
        self.draw[player].text((80, 1), f'{p:4d}', font=self.font1, fill=255)
        if p <= config.DOUBT_TIMEOUT:
            self.draw[player].text(MSG_DOUBT_COORD, MSG_DOUBT,
                            font=MSG_DOUBT_FONT, fill=255)
        self.display(player)
        self.oled.image(self.image[player])
        self.oled.show()

    def clear(self):
        for i in range(0, 2):
            self.display(i)
            self.oled.fill(0)
        # self.oled.show()

    def clear_message(self, disp=None) -> None:
        if disp is None:
            for i in range(0,2):
                self.draw[i].rectangle((0, 0, self.oled.width, 24), fill=0)
                self.display(i)
                self.oled.image(self.image[i])
                self.oled.show()
        else:
            self.draw[disp].rectangle((0, 0, self.oled.width, 24), fill=0)
            self.display(disp)
            self.oled.image(self.image[disp])
            self.oled.show()


    def show(self, player=None) -> None:
        if player is None:
            for i in range(0,2):
                self.display(i)
                self.oled.image(self.image[i])
                self.oled.show()
        else:
            self.display(player)
            self.oled.image(self.image[player])
            self.oled.show()
