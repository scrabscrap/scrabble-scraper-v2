
import logging

import adafruit_ssd1306
import board
from PIL import Image, ImageDraw, ImageFont

from config import config
from display import Display

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(module)s - %(levelname)s - %(message)s')


class OledDisplay(Display):

    def __init__(self):
        # todo: 2nd display
        self.i2c = board.I2C()
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c, addr=0x3C)
        self.font_family = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
        self.font = ImageFont.truetype(self.font_family, 42)
        self.font1 = ImageFont.truetype(self.font_family, 20)
        self.font2 = ImageFont.truetype(self.font_family, 10)
        self.image = Image.new('1', (self.oled.width, self.oled.height))
        self.empty = Image.new('1', (self.oled.width, self.oled.height))
        self.draw = ImageDraw.Draw(self.image)

    def show_boot(self):
        MSG_BOOT = 'Boot'
        MSG_BOOT_FONT = self.font
        (msg_boot_width, _) = MSG_BOOT_FONT.getsize(MSG_BOOT)
        MSG_BOOT_COORD = (self.oled.width // 2 - msg_boot_width // 2, 20)
        logging.debug('Boot message')
        self.image.paste(self.empty)
        self.draw.text(MSG_BOOT_COORD, MSG_BOOT, font=MSG_BOOT_FONT, fill=255)
        self.oled.image(self.image)
        self.oled.show()

    def show_ready(self):
        MSG_READY = 'Ready'
        MSG_READY_FONT = self.font
        (msg_ready_width, _) = MSG_READY_FONT.getsize(MSG_READY)
        MSG_READY_COORD = (self.oled.width // 2 - msg_ready_width // 2, 20)
        logging.debug('Ready message')
        self.image.paste(self.empty)
        self.draw.text(MSG_READY_COORD, MSG_READY,
                       font=MSG_READY_FONT, fill=255)
        self.oled.image(self.image)
        self.oled.show()

    def show_pause(self):
        MSG_BREAK = 'Pause'
        MSG_BREAK_FONT = self.font1
        MSG_BREAK_COORD = (24, 1)
        self.draw.text(MSG_BREAK_COORD, MSG_BREAK,
                       font=MSG_BREAK_FONT, fill=255)
        self.oled.invert(True)
        self.oled.image(self.image)
        self.oled.show()
        ## todo: check

    def add_malus(self, player):
        MSG_MALUS = '-10P'
        MSG_MALUS_FONT = self.font1
        # (msg_malus_width, _) = MSG_MALUS_FONT.getsize(MSG_MALUS)
        MSG_MALUS_COORD = (24, 1)
        (w, h) = MSG_MALUS_FONT.getsize(MSG_MALUS)
        logging.debug(f'size: w{w:d}/h{h:d}')

        if player == 0:
            logging.debug('(0) malus -10')
            self.draw.rectangle((24, 0, 90, 24), fill=0)
            self.draw.text(MSG_MALUS_COORD, MSG_MALUS,
                           font=MSG_MALUS_FONT, fill=255)
        elif player == 1:
            logging.debug('(1) malus -10')
            # todo: 2nd display
            # self.draw.text(MSG_MALUS_COORD, MSG_MALUS, font=MSG_MALUS_FONT, fill=255)
        self.oled.image(self.image)
        self.oled.show()

    def add_remove_tiles(self, player):
        MSG_REMOVE_TILES = '\u2717Zug\u270D'
        MSG_REMOVE_TILES_FONT = self.font1
        # (msg_remove_width, _) = MSG_REMOVE_TILES_FONT.getsize(MSG_REMOVE_TILES)
        MSG_REMOVE_TILES_COORD = (24, 1)
        (w, h) = MSG_REMOVE_TILES_FONT.getsize(MSG_REMOVE_TILES)
        logging.debug(f'size: w{w:d}/h{h:d}')

        if player == 0:
            logging.debug('(0) Entf. Zug')
            self.draw.rectangle((24, 0, 90, 24), fill=0)
            self.draw.text(MSG_REMOVE_TILES_COORD, MSG_REMOVE_TILES,
                           font=MSG_REMOVE_TILES_FONT, fill=255)
        elif player == 1:
            logging.debug('(1) Entf. Zug')
            # todo: 2nd display
            # self.draw.text(MSG_MALUS_COORD, MSG_MALUS, font=MSG_MALUS_FONT, fill=255)
        self.oled.image(self.image)
        self.oled.show()

    def show_cam_err(self):
        MSG_ERR_CAM = '\u2620Cam'
        MSG_ERR_CAM_FONT = self.font
        MSG_ERR_CAM_COORD = (1, 16)
        logging.debug('Cam Err')
        self.draw.text(MSG_ERR_CAM_COORD, MSG_ERR_CAM,
                       font=MSG_ERR_CAM_FONT, fill=255)
        self.oled.image(self.image)
        self.oled.show()

    def show_ftp_err(self):
        MSG_ERR_FTP = '\u2620ftp'
        MSG_ERR_FTP_FONT = self.font
        MSG_ERR_FTP_COORD = (1, 16)
        logging.debug('FTP Err')
        
        self.draw.text(MSG_ERR_FTP_COORD, MSG_ERR_FTP,
                       font=MSG_ERR_FTP_FONT, fill=255)
        self.oled.image(self.image)
        self.oled.show()

    def show_config(self):
        MSG_CONFIG = '\u270ECfg'
        MSG_CONFIG_FONT = self.font
        MSG_CONFIG_COORD = (1, 16)
        logging.debug('Cfg')
        self.draw.text(MSG_CONFIG_COORD, MSG_CONFIG,
                       font=MSG_CONFIG_FONT, fill=255)
        self.oled.image(self.image)
        self.oled.show()

    def add_time(self, player, t1, p1, t2, p2):
        self.image.paste(self.empty)
        MSG_DOUBT = '\u2049'  # \u2718
        MSG_DOUBT_FONT = self.font1
        (msg_doubt_width, _) = MSG_DOUBT_FONT.getsize(MSG_DOUBT)
        MSG_DOUBT_COORD = (1, 0)

        # display 0
        if player == 0:
            m1, s1 = divmod(abs(config.MAX_TIME - t1), 60)
            left = f'-{m1:1d}:{s1:02d}' if config.MAX_TIME - \
                t1 < 0 else f'{m1:02d}:{s1:02d}'
            self.draw.text((1, 22), left, font=self.font, fill=255)
            self.draw.text((80, 1), f'{p1:4d}', font=self.font1, fill=255)
            if player == 0 and p1 <= config.DOUBT_TIMEOUT:
                self.draw.text(MSG_DOUBT_COORD, MSG_DOUBT,
                               font=MSG_DOUBT_FONT, fill=255)
        elif player == 1:
            # display 1
            m2, s2 = divmod(abs(config.MAX_TIME - t2), 60)
            right = f'-{m2:1d}:{s2:02d}' if config.MAX_TIME - \
                t2 < 0 else f'{m2:02d}:{s2:02d}'
        self.oled.image(self.image)
        self.oled.show()

    def clear(self):
        self.oled.fill(0)
        self.oled.invert(False)
        # self.oled.show()

    def show(self):
        self.oled.image(self.image)
        self.oled.show()
