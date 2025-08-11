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
from time import sleep

import ifaddr
from luma.core.error import DeviceNotFoundError
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106, ssd1306
from PIL import Image, ImageDraw, ImageFont

from config import config
from display import Display

# docu https://luma-oled.readthedocs.io/en/latest/index.html
IC2_PORT_PLAYER1 = 1
IC2_ADDRESS_PLAYER1 = 0x3C
IC2_PORT_PLAYER2 = 3
IC2_ADDRESS_PLAYER2 = 0x3C


def test_display(serial, device_cls):
    """test if device is available"""
    try:
        device = device_cls(serial)
        image = Image.new('1', device.size)
        draw = ImageDraw.Draw(image)
        draw.rectangle((device.width - 10, device.height - 10, device.width - 1, device.height - 1), outline=255, fill=255)
        device.display(image)
        sleep(0.1)  # Kurze Anzeigezeit
        device.clear()
        device.show()
        return device
    except Exception:  # pylint: disable=broad-exception-caught
        return None


def detect_device(serial):
    """detect device ssh1306 or sh1106"""
    device = test_display(serial, sh1106)
    if device:
        return device

    # SSD1306 probieren
    device = test_display(serial, ssd1306)
    if device:
        return device

    raise RuntimeError('OLED-Typ konnte nicht erkannt werden')


try:
    SERIAL: tuple[i2c, i2c] = (
        i2c(port=IC2_PORT_PLAYER1, address=IC2_ADDRESS_PLAYER1),
        i2c(port=IC2_PORT_PLAYER2, address=IC2_ADDRESS_PLAYER2),
    )

    DEVICE: tuple[ssd1306 | sh1106, ssd1306 | sh1106] = (detect_device(SERIAL[0]), detect_device(SERIAL[1]))

except (OSError, DeviceNotFoundError, RuntimeError) as e:
    if not config.is_testing:
        logging.basicConfig(filename=f'{config.path.log_dir}/messages.log', level=logging.INFO, force=True)
        logging.getLogger().error(f'error opening OLED 1 / OLED 2 {type(e).__name__}: {e}')
    raise RuntimeError('Error: OLED 1 / OLED 2 not available') from e

BLACK = 'black'
WHITE = 'white'

FONT_FAMILY = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
FONT = ImageFont.truetype(FONT_FAMILY, 40)  # time
FONT1 = ImageFont.truetype(FONT_FAMILY, 20)
FONT2 = ImageFont.truetype(FONT_FAMILY, 14)  # only nickname
FONT3 = ImageFont.truetype(FONT_FAMILY, 10)  # nickname and show score

MIDDLE = (64, 44)
IP_STR_COORD = (64, 3)
DOUBT_STR_COORD = (0, 3)
INFO_STR_COORD = (14, 11)
TIMER_STR_COORD = (128, 3)
END_NICK_COORD = (2, 5)
END_MSG_COORD = (2, 30)

logger = logging.getLogger()


class OLEDDisplay(Display):
    """Implementation of class Display with OLED"""

    def stop(self) -> None:
        logger.debug('display stop')
        for i in range(2):
            DEVICE[i].hide()

    def show_ready(self, msg=('Ready', 'Ready')) -> None:
        def get_ipv4_address() -> tuple:
            ips = {adapter.name: ip.ip for adapter in ifaddr.get_adapters() for ip in adapter.ips if ip.is_IPv4}
            return (ips.get('wlan0', 'n/a'), ips.get('eth0', 'n/a'))

        def draw_letter_row(draw, letters, x_start, y0):
            for i, letter in enumerate(letters):
                x0 = x_start + i * 20
                x1 = x0 + 18
                draw.rounded_rectangle((x0, y0, x1, y0 + 18), fill=WHITE, radius=4)
                draw.text((x0 + 9, y0 + 9), letter, font=FONT2, fill=BLACK, anchor='mm', align='center', stroke_width=0)

        logger.debug(f'show message {msg}')
        title = ('', '') if self.game is not None else get_ipv4_address()
        with canvas(DEVICE[0]) as draw:
            draw.text(IP_STR_COORD, title[0], font=FONT3, fill=WHITE, anchor='mt', align='center')
            if msg[0] == 'SCRABSCRAP':
                draw_letter_row(draw, 'SCRAB', x_start=5, y0=18)
                draw_letter_row(draw, 'SCRAP', x_start=25, y0=40)
            else:
                draw.text(MIDDLE, f'{msg[0]:.10s}', font=FONT1, fill=WHITE, anchor='mm', align='center')

        with canvas(DEVICE[1]) as draw:
            draw.text(IP_STR_COORD, title[1], font=FONT3, fill=WHITE, anchor='mt', align='center')
            draw.text(MIDDLE, f'{msg[1]:.10s}', font=FONT1, fill=WHITE, anchor='mm', align='center')

    def show_end_of_game(self) -> None:
        if self.game:
            for i in range(2):
                DEVICE[i].clear()
                with canvas(DEVICE[i]) as draw:
                    draw.text(END_NICK_COORD, f'{self.game.nicknames[i]:10.10s}', font=FONT1, fill=WHITE)
                    if self.game.moves:
                        minutes, seconds = divmod(abs(config.scrabble.max_time - self.game.moves[-1].played_time[i]), 60)
                        score = self.game.moves[-1].score[i]
                        draw.text(END_MSG_COORD, f'{minutes:02d}:{seconds:02d}  {score:3d}', font=FONT1, fill=WHITE)

    def render_display(
        self, player: int, played_time: tuple[int, int], current: tuple[int, int], info: str | None = None
    ) -> None:
        def _format_time(played: int) -> str:
            delta = config.scrabble.max_time - played
            minutes, seconds = divmod(abs(delta), 60)
            return f'-{minutes:1d}:{seconds:02d}' if delta < 0 else f'{minutes:02d}:{seconds:02d}'

        def _get_score(i: int) -> int:
            return self.game.moves[-1].score[i] if self.game and self.game.moves else 0

        def _draw_player_info(draw, i: int, is_active: bool, time_str: str, info: str | None) -> None:
            color = BLACK if info and is_active else WHITE

            if is_active and info:
                draw.rectangle((0, 0, 128, 64), fill=WHITE)

            if is_active and 0 < current[player] <= config.scrabble.doubt_timeout:
                draw.text(DOUBT_STR_COORD, '?', font=FONT1, fill=color, anchor='lt')

            if is_active and current[player] > 0:
                draw.text(TIMER_STR_COORD, f'{current[player]:3d}', font=FONT1, fill=color, anchor='rt')

            if info:
                if config.scrabble.show_score:
                    draw.text(INFO_STR_COORD, f'{info:6.5s}{_get_score(i):3d}', font=FONT2, fill=color, anchor='lm')
                else:
                    draw.text(INFO_STR_COORD, f'{info:9.9s}', font=FONT2, fill=color, anchor='lm')
            else:
                if config.scrabble.show_score:
                    draw.text(INFO_STR_COORD, f'{nicknames[i]:6.5s}{_get_score(i):3d}', font=FONT2, fill=color, anchor='lm')
                else:
                    draw.text(INFO_STR_COORD, f'{nicknames[i]:9.9s}', font=FONT2, fill=color, anchor='lm')

            draw.text(MIDDLE, time_str, font=FONT, fill=color, anchor='mm', align='center')

        nicknames = self.game.nicknames if self.game else ('n/a', 'n/a')

        for i in range(2):
            time_str = _format_time(played_time[i])
            is_active = i == player

            if info:
                DEVICE[i].clear()

            with canvas(DEVICE[i]) as draw:
                _draw_player_info(draw, i, is_active, time_str, info)
