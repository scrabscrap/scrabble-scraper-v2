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
from concurrent.futures import Future
import logging
import time
import random
from typing import Optional


def move(waitfor: Optional[Future], game, img):
    counter = int(round(time.time() * 1000))
    logging.debug(f'move {counter}')
    # todo: check why this solution is not correct?
    # if waitfor is not None:
    #     done, not_done = futures.wait({waitfor})
    #     assert len(done) == 0, 'error on wait to future'
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    time.sleep(random.randint(10, 40) / 10)  # between 1s and 4s
    logging.debug(f'move {counter} ready')


def valid_challenge(waitfor: Optional[Future], game):
    counter = int(round(time.time() * 1000))
    logging.debug(f'valid challenge {counter}')
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    time.sleep(0.1)
    logging.debug(f'valid challenge {counter} ready')


def invalid_challenge(waitfor: Optional[Future], game):
    counter = int(round(time.time() * 1000))
    logging.debug(f'invalid challenge {counter}')
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    time.sleep(0.1)
    logging.debug(f'invalid challenge {counter} ready')


def end_of_game(waitfor: Optional[Future]):
    counter = int(round(time.time() * 1000))
    logging.debug(f'end of game {counter}')
    while waitfor is not None and waitfor.running():
        time.sleep(0.05)
    time.sleep(1.5)
    logging.debug(f'end of game {counter} ready')
