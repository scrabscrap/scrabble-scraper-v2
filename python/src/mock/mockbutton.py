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
from time import sleep

import cv2
from button import ButtonEnum
from config import config

try:
    import RPi.GPIO  # type: ignore
except ImportError:
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory

    Device.pin_factory = MockFactory()  # set default pin factory

    pin_green = Device.pin_factory.pin(ButtonEnum.GREEN.value)
    pin_yellow = Device.pin_factory.pin(ButtonEnum.YELLOW.value)
    pin_red = Device.pin_factory.pin(ButtonEnum.RED.value)
    pin_doubt1 = Device.pin_factory.pin(ButtonEnum.DOUBT1.value)
    pin_doubt2 = Device.pin_factory.pin(ButtonEnum.DOUBT2.value)
    pin_reset = Device.pin_factory.pin(ButtonEnum.RESET.value)
    pin_reboot = Device.pin_factory.pin(ButtonEnum.REBOOT.value)
    pin_config = Device.pin_factory.pin(ButtonEnum.CONFIG.value)

    def listen_keyboard():
        logging.info('listen keyboard')
        if config.KEYBOARD:
            print('(g)reen (r)ed (y)ellow doubt(1) doubt(2) (c)config (q)uit re(s)et')
        while True:
            key = cv2.waitKey(0 if config.SIMULATE else 1) & 0xff
            if (key == 27) or (key == ord('q')):
                print('pressed (q)uit - wait 3s')
                pin_reboot.drive_high()
                sleep(3)
                pin_reboot.drive_low()
                sleep(0.01)
                break
            if key == ord('g'):
                print('pressed (g)reen')
                pin_green.drive_high()
                sleep(0.01)
                pin_green.drive_low()
            if key == ord('r'):
                print('pressed (r)ed')
                pin_red.drive_high()
                sleep(0.01)
                pin_red.drive_low()
            if key == ord('y'):
                print('pressed (y)ellow')
                pin_yellow.drive_high()
                sleep(0.01)
                pin_yellow.drive_low()
            if key == ord('1'):
                print('pressed (1)doubt')
                pin_doubt1.drive_high()
                sleep(0.01)
                pin_doubt1.drive_low()
            if key == ord('2'):
                print('pressed (2)doubt')
                pin_doubt2.drive_high()
                sleep(0.01)
                pin_doubt2.drive_low()
            if key == ord('s'):
                print('pressed re(s)et - wait 3s')
                pin_reset.drive_high()
                sleep(3)
                pin_reset.drive_low()
            if key == ord('c'):
                print('pressed (c)onfig - wait 3s')
                pin_config.drive_high()
                sleep(3)
                pin_config.drive_low()
            sleep(0.01)
