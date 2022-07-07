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
import random
import time
from concurrent.futures import Future
from typing import Optional

import cv2


def move(waitfor: Optional[Future], game, img):
    logging.debug('move entry')
    # todo: check why this solution is not correct?
    # if waitfor is not None:
    #     done, not_done = futures.wait({waitfor})
    #     assert len(done) == 0, 'error on wait to future'
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)

    counter = int(round(time.time() * 1000))
    logging.debug(f'before write /home/pi/scrabscrapv2/python/{counter}.jpg: {len(img)}')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(f'/home/pi/scrabscrapv2/python/{counter}.jpg', gray)
    logging.debug(f'after write {counter}.jpg')
    time.sleep(random.randint(10, 40) / 10)  # between 1s and 4s
    logging.debug('move exit')


def valid_challenge(waitfor: Optional[Future], game):
    logging.debug('valid_challenge entry')
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    time.sleep(0.1)
    logging.debug('valid_challenge exit')


def invalid_challenge(waitfor: Optional[Future], game):
    logging.debug('invalid_challenge entry')
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    time.sleep(0.1)
    logging.debug('invalid_challenge exit')


def end_of_game(waitfor: Optional[Future]):
    logging.debug('end_of_game entry')
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    time.sleep(1.5)
    logging.debug('end_of_games exit')
