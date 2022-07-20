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
import time
from signal import alarm
from typing import Callable, Optional

from config import config
from hardware.led import LED, LEDEnum
from processing import end_of_game, invalid_challenge, move, valid_challenge
from scrab import Game
from scrabblewatch import ScrabbleWatch
from threadpool import pool
from util import singleton


@singleton
class State:

    def __init__(self, cam=None, watch: Optional[ScrabbleWatch] = None) -> None:
        self.current_state: str = 'START'
        self.watch: ScrabbleWatch = watch if watch is not None else ScrabbleWatch()
        self.cam = cam
        self.last_submit = None  # last submit to thread pool; waiting for processing of the last move
        self.bounce = {'GREEN': .0, 'RED': .0, 'YELLOW': .0, 'DOUBT0': .0,
                       'DOUBT1': .0, 'RESET': .0, 'CONFIG': .0, 'REBOOT': .0}
        self.game: Game = Game(None)
        atexit.register(self._atexit)

    def _atexit(self) -> None:
        logging.info('atexit State')
        pass

    def do_ready(self) -> str:
        """Game can be started"""
        self.watch.display.show_ready()
        self.current_state = 'START'
        return self.current_state

    def do_start0(self) -> str:
        """Start playing with player 0"""
        logging.debug(f'{self.current_state} - (start) -> S0')
        self.watch.start(0)
        LED.switch_on({LEDEnum.green})  # turn on LED green
        return 'S0'

    def do_start1(self) -> str:
        """Start playing with player 1"""
        logging.debug(f'{self.current_state} - (start) -> S1')
        self.watch.start(1)
        LED.switch_on({LEDEnum.red})  # turn on LED red
        return 'S1'

    def do_move0(self) -> str:
        """analyze players 0 move"""
        logging.debug(f'{self.current_state} - (move) -> S1')
        _, t0, _, t1, _ = self.watch.get_status()
        # next player
        self.watch.start(1)
        LED.switch_on({LEDEnum.red})  # turn on LED red

        picture = self.cam.read()  # type: ignore
        self.last_submit = pool.submit(move, self.last_submit, self.game, picture, 0, (t0, t1))
        return 'S1'

    def do_move1(self) -> str:
        """analyze players 1 move"""
        logging.debug(f'{self.current_state} - (move) -> S0')
        _, t0, _, t1, _ = self.watch.get_status()
        # next player
        self.watch.start(0)
        LED.switch_on({LEDEnum.green})  # turn on LED green

        picture = self.cam.read()  # type: ignore
        self.last_submit = pool.submit(move, self.last_submit, self.game, picture, 1, (t0, t1))
        return 'S0'

    def do_pause0(self) -> str:
        """pause pressed while player 0 is active"""
        logging.debug(f'{self.current_state} - (pause) -> P0')
        self.watch.pause()
        LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green, yellow
        return 'P0'

    def do_pause1(self) -> str:
        """pause pressed while player 1 is active"""
        logging.debug(f'{self.current_state} - (pause) -> P1')
        self.watch.pause()
        LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
        return 'P1'

    def do_resume0(self) -> str:
        """resume from pause while player 0 is active"""
        logging.debug(f'{self.current_state} - (resume) -> S0')
        self.watch.resume()
        LED.switch_on({LEDEnum.green})  # turn on LED green
        return 'S0'

    def do_resume1(self) -> str:
        """resume from pause while player 1 is active"""
        logging.debug(f'{self.current_state} - (resume) -> S1')
        self.watch.resume()
        LED.switch_on({LEDEnum.red})  # turn on LED red
        return 'S1'

    def do_valid_challenge0(self) -> str:
        """player 0 has a valid challenge for the last move from player 1"""
        logging.debug(f'{self.current_state} - (valid challenge) -> P0')
        _, t0, _, t1, _ = self.watch.get_status()
        self.watch.display.add_remove_tiles(1)  # player 1 has to remove the last move
        self.last_submit = pool.submit(valid_challenge, self.last_submit, self.game, 0, (t0, t1))
        LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green, yellow
        return 'P0'

    def do_valid_challenge1(self) -> str:
        """player 1 has a valid challenge for the last move from player 0"""
        logging.debug(f'{self.current_state} - (valid challenge) -> P1')
        _, t0, _, t1, _ = self.watch.get_status()
        self.watch.display.add_remove_tiles(0)  # player 0 has to remove the last move
        self.last_submit = pool.submit(valid_challenge, self.last_submit, self.game, 1, (t0, t1))
        LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
        return 'P1'

    def do_invalid_challenge0(self) -> str:
        """player 0 has an invalid challenge for the last move from player 1"""
        logging.debug(
            f'{self.current_state} - (invalid challenge) -> P0 (-{config.MALUS_DOUBT:2d})')  # -10
        _, t0, _, t1, _ = self.watch.get_status()
        self.watch.display.add_malus(0)  # player 0 gets a malus
        self.last_submit = pool.submit(invalid_challenge, self.last_submit, self.game, 0, (t0, t1))
        LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green
        return 'P0'

    def do_invalid_challenge1(self) -> str:
        """player 0 has an invalid challenge for the last move from player 1"""
        logging.debug(
            f'{self.current_state} - (invalid challenge) -> P1 (-{config.MALUS_DOUBT:2d})')  # -10
        _, t0, _, t1, _ = self.watch.get_status()
        self.watch.display.add_malus(1)  # player 1 gets a malus
        self.last_submit = pool.submit(invalid_challenge, self.last_submit, self.game, 1, (t0, t1))
        LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
        return 'P1'

    def do_reset(self) -> str:
        """Resets state and game to default"""
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
        """Perform a reboot"""
        logging.debug(f'{self.current_state} - (reboot) -> START')
        self.watch.display.show_boot()  # Display message REBOOT
        # todo: check for upload
        LED.switch_on({})  # type: ignore
        self.last_submit = pool.submit(end_of_game, self.last_submit)
        self.watch.display.stop()
        current_state = 'START'
        alarm(1)  # raise alarm for reboot
        return current_state

    def do_config(self) -> str:
        """??? necessary ???"""
        logging.debug(f'{self.current_state} - (config) -> START')
        self.watch.reset()
        self.watch.display.show_config()  # Display message CONFIG
        # todo: check for upload
        LED.switch_on({})  # type: ignore
        current_state = 'START'
        return current_state

    def press_button(self, button: str) -> None:
        """process button press

        before sending the next event, press button will wait for self.bounce
        """
        try:
            press = time.time()
            if press < self.bounce[button] + 0.1:
                pass
            else:
                self.current_state = self.state[(self.current_state, button.lower())](self)
        except KeyError:
            logging.debug('Key Error - ignore')

    def release_button(self, button: str) -> None:
        """process button release

        sets the release time to self.bounce
        """
        self.bounce[button] = time.time()

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
