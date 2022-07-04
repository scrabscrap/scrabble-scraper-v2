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
import atexit
import logging
from signal import alarm
from typing import Callable, Optional

from config import config
from led import LED, LEDEnum
from processing import end_of_game, invalid_challenge, move, valid_challenge
from scrabblewatch import ScrabbleWatch
from threadpool import pool
from util import singleton


@singleton
class State:

    def __init__(self, cam=None, watch: Optional[ScrabbleWatch] = None) -> None:
        self.current_state: str = 'START'
        self.watch: ScrabbleWatch = watch if watch is not None else ScrabbleWatch()
        self.cam = cam
        atexit.register(self._atexit)

    def _atexit(self) -> None:
        logging.info('atexit State')
        pass

    def do_ready(self) -> str:
        self.watch.display.show_ready()
        self.current_state = 'START'
        return self.current_state

    def do_start0(self) -> str:
        logging.debug(f'{self.current_state} - (start) -> S0')
        self.watch.start(0)
        LED.switch_on({LEDEnum.green})  # turn on LED green
        return 'S0'

    def do_move0(self) -> str:

        p, t0, c0, t1, c1 = self.watch.get_status()
        # next player
        logging.debug(f'{self.current_state} - (move) -> S1')
        self.watch.start(1)
        LED.switch_on({LEDEnum.red})  # turn on LED red

        # get picture
        # analyze
        # calc move
        # store move
        picture = self.cam.read()  # type: ignore
        pool.submit(move, None, None, picture)
        return 'S1'

    def do_pause0(self) -> str:
        logging.debug(f'{self.current_state} - (pause) -> P0')
        self.watch.pause()
        # turn on LED green, yellow
        LED.switch_on({LEDEnum.green, LEDEnum.yellow})
        return 'P0'

    def do_resume0(self) -> str:
        logging.debug(f'{self.current_state} - (resume) -> S0')
        self.watch.resume()
        LED.switch_on({LEDEnum.green})  # turn on LED green
        return 'S0'

    def do_valid_challenge0(self) -> str:
        logging.debug(f'{self.current_state} - (valid challenge) -> P0')
        self.watch.display.add_remove_tiles(1)
        pool.submit(valid_challenge, None, None)
        # turn on LED green, yellow
        LED.switch_on({LEDEnum.green, LEDEnum.yellow})
        return 'P0'

    def do_invalid_challenge0(self) -> str:
        logging.debug(
            f'{self.current_state} - (invalid challenge) -> P0 (-{config.MALUS_DOUBT:2d})')  # -10
        self.watch.display.add_malus(0)  # player 1
        LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green
        pool.submit(invalid_challenge, None, None)
        return 'P0'

    def do_start1(self) -> str:
        logging.debug(f'{self.current_state} - (start) -> S1')
        self.watch.start(1)
        LED.switch_on({LEDEnum.red})  # turn on LED red
        return 'S1'

    def do_move1(self) -> str:
        p, t1, c1, t2, c2 = self.watch.get_status()
        # next state
        logging.debug(f'{self.current_state} - (move) -> S0')
        self.watch.start(0)
        LED.switch_on({LEDEnum.green})  # turn on LED green
        picture = self.cam.read()  # type: ignore
        pool.submit(move, None, None, picture)
        return 'S0'

    def do_resume1(self) -> str:
        logging.debug(f'{self.current_state} - (resume) -> S1')
        self.watch.resume()
        LED.switch_on({LEDEnum.red})  # turn on LED red
        return 'S1'

    def do_pause1(self) -> str:
        logging.debug(f'{self.current_state} - (pause) -> P1')
        self.watch.pause()
        LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
        return 'P1'

    def do_valid_challenge1(self) -> str:
        logging.debug(f'{self.current_state} - (valid challenge) -> P1')
        self.watch.display.add_remove_tiles(0)
        pool.submit(valid_challenge, None, None)
        LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
        return 'P1'

    def do_invalid_challenge1(self) -> str:
        logging.debug(
            f'{self.current_state} - (invalid challenge) -> P1 (-{config.MALUS_DOUBT:2d})')  # -10
        self.watch.display.add_malus(1)  # player 2
        pool.submit(invalid_challenge, None, None)
        LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
        return 'P1'

    def do_reset(self) -> str:
        logging.debug(f'{self.current_state} - (reset) -> START')
        LED.switch_on({})  # type: ignore
        self.watch.reset()
        # todo: check for upload
        # todo: reset app data
        current_state = 'START'
        self.do_ready()
        pool.submit(end_of_game, None)
        return current_state

    def do_reboot(self) -> str:
        logging.debug(f'{self.current_state} - (reboot) -> START')
        self.watch.display.show_boot()  # Display message REBOOT
        # todo: check for upload
        LED.switch_on({})  # type: ignore
        pool.submit(end_of_game, None)
        self.watch.display.stop()
        current_state = 'START'
        alarm(1)
        return current_state

    def do_config(self) -> str:
        logging.debug(f'{self.current_state} - (config) -> START')
        self.watch.reset()
        self.watch.display.show_config()  # Display message CONFIG
        # todo: check for upload
        LED.switch_on({})  # type: ignore
        current_state = 'START'
        return current_state

    def press_button(self, button: str) -> None:
        # logging.debug(f'button press: {button}')
        try:
            self.current_state = self.state[(
                self.current_state, button.lower())](self)
        except KeyError:
            logging.debug('Key Error - ignore')

    def release_button(self, button: str) -> None:
        logging.debug(f'button release: {button}')

    # START, pause => not supported
    state: dict[tuple[str, str], Callable] = {
        ('START', 'green'): do_start1,
        ('START', 'red'): do_start0,
        ('START', 'reset'): do_reset,
        ('START', 'reboot'): do_reboot,
        ('START', 'config'): do_config,
        ('S0', 'green'): do_move0,
        ('S0', 'yellow'): do_pause0,
        ('P0', 'red'): do_resume0,
        ('P0', 'yellow'): do_resume0,
        ('P0', 'doubt0'): do_valid_challenge0,
        ('P0', 'doubt1'): do_invalid_challenge0,
        ('P0', 'reset'): do_reset,
        ('P0', 'reboot'): do_reboot,
        ('P0', 'config'): do_config,
        ('S1', 'red'): do_move1,
        ('S1', 'yellow'): do_pause1,
        ('P1', 'green'): do_resume1,
        ('P1', 'yellow'): do_resume1,
        ('P1', 'doubt1'): do_valid_challenge1,
        ('P1', 'doubt0'): do_invalid_challenge1,
        ('P1', 'reset'): do_reset,
        ('P1', 'reboot'): do_reboot,
        ('P1', 'config'): do_config,
    }
