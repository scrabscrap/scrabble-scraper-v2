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
from luma.core.interface.serial import i2c  # type: ignore
from luma.core.render import canvas  # type: ignore
from luma.oled.device import ssd1306  # type: ignore
from PIL import ImageFont

IC2_PORT_PLAYER1 = 1
IC2_ADDRESS_PLAYER1 = 0x3c
IC2_PORT_PLAYER2 = 3
IC2_ADDRESS_PLAYER2 = 0x3c
WHITE = 'white'
MIDDLE = (64, 42)

# docu https://luma-oled.readthedocs.io/en/latest/index.html


FONT_FAMILY = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
font = ImageFont.truetype(FONT_FAMILY, 20)

serial: tuple[i2c, i2c] = (
    i2c(port=IC2_PORT_PLAYER1, address=IC2_ADDRESS_PLAYER1),
    i2c(port=IC2_PORT_PLAYER2, address=IC2_ADDRESS_PLAYER2))
device: tuple[ssd1306, ssd1306] = (
    ssd1306(serial[0]), ssd1306(serial[1]))


def do_nothing(obj):  # pylint: disable=W0613
    """empty funtion to preserve oled display"""
    pass


# do not turn off display at exit
# override the cleanup method
device[0].cleanup = do_nothing  # type: ignore
device[1].cleanup = do_nothing  # type: ignore

for i in range(2):
    with canvas(device[i]) as draw:
        draw.text(MIDDLE, 'Loading ...', font=font, anchor='mm', align='center', fill=WHITE)
