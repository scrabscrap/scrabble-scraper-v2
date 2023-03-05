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
import gc
import logging
import threading
from concurrent.futures import Future
from signal import alarm
from typing import Callable, Optional

from config import config
from hardware.button import Button
from hardware.led import LED, LEDEnum
from processing import (end_of_game, invalid_challenge, move, start_of_game,
                        store_status, valid_challenge)
from scrabble import Game
from scrabblewatch import ScrabbleWatch
from threadpool import pool
from util import Singleton

# states
START = 'START'
S0 = 'S0'
S1 = 'S1'
P0 = 'P0'
P1 = 'P1'
EOG = 'EOG'  # end of game
# buttons
GREEN = 'GREEN'
YELLOW = 'YELLOW'
RED = 'RED'
DOUBT0 = 'DOUBT0'
DOUBT1 = 'DOUBT1'
RESET = 'RESET'
REBOOT = 'REBOOT'
AP = 'AP'


class State(metaclass=Singleton):  # pylint: disable=R0904
    """State machine of the scrabble game"""

    def __init__(self, cam=None, watch: Optional[ScrabbleWatch] = None, button_handler: Optional[Button] = None) -> None:
        self.current_state: str = START
        self.watch: ScrabbleWatch = watch if watch else ScrabbleWatch()
        self.button_handler: Button = button_handler if button_handler else Button()
        self.cam = cam
        self.last_submit: Optional[Future] = None  # last submit to thread pool; waiting for processing of the last move
        self.game: Game = Game(None)
        self.picture = None
        self.op_event = threading.Event()

    def init(self) -> None:
        """init state machine"""
        self.button_handler.start(func_pressed=self.press_button)
        self.do_new_game()

    def do_ready(self) -> str:
        """Game can be started"""
        logging.debug(f'{self.game.nicknames}')
        self.watch.display.show_ready(self.game.nicknames)
        self.watch.display.set_game(self.game)
        self.picture = self.cam.read(peek=True) if self.cam else None  # type: ignore
        self.current_state = START
        return self.current_state

    def do_start0(self) -> str:
        """Start playing with player 0"""
        logging.info(f'{self.current_state} - (start) -> {S0}')
        self.watch.start(0)
        LED.switch_on({LEDEnum.green})  # turn on LED green
        self.watch.display.render_display(1, [0, 0], [0, 0])
        return S0

    def do_start1(self) -> str:
        """Start playing with player 1"""
        logging.info(f'{self.current_state} - (start) -> {S1}')
        self.watch.start(1)
        LED.switch_on({LEDEnum.red})  # turn on LED red
        self.watch.display.render_display(0, [0, 0], [0, 0])
        return S1

    def do_move0(self) -> str:
        """analyze players 0 move"""
        logging.info(f'{self.current_state} - (move) -> {S1}')
        _, (time0, time1), _ = self.watch.status()
        # next player
        self.watch.start(1)
        LED.switch_on({LEDEnum.red})  # turn on LED red
        self.picture = self.cam.read()  # type: ignore
        self.last_submit = pool.submit(move, self.last_submit, self.game, self.picture, 0, (time0, time1), self.op_event)
        return S1

    def do_move1(self) -> str:
        """analyze players 1 move"""
        logging.info(f'{self.current_state} - (move) -> {S0}')
        _, (time0, time1), _ = self.watch.status()
        # next player
        self.watch.start(0)
        LED.switch_on({LEDEnum.green})  # turn on LED green

        self.picture = self.cam.read()  # type: ignore
        self.last_submit = pool.submit(move, self.last_submit, self.game, self.picture, 1, (time0, time1), self.op_event)
        return S0

    def do_pause0(self) -> str:
        """pause pressed while player 0 is active"""
        logging.info(f'{self.current_state} - (pause) -> {P0}')
        self.watch.pause()
        LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green, yellow
        return P0

    def do_pause1(self) -> str:
        """pause pressed while player 1 is active"""
        logging.info(f'{self.current_state} - (pause) -> {P1}')
        self.watch.pause()
        LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
        return P1

    def do_resume0(self) -> str:
        """resume from pause while player 0 is active"""
        logging.info(f'{self.current_state} - (resume) -> {S0}')
        self.watch.resume()
        LED.switch_on({LEDEnum.green})  # turn on LED green
        return S0

    def do_resume1(self) -> str:
        """resume from pause while player 1 is active"""
        logging.info(f'{self.current_state} - (resume) -> {S1}')
        self.watch.resume()
        LED.switch_on({LEDEnum.red})  # turn on LED red
        return S1

    def do_valid_challenge0(self) -> str:
        """player 0 has a valid challenge for the last move from player 1"""
        logging.info(f'{self.current_state} - (valid challenge) -> {P0}')
        _, played_time, current = self.watch.status()
        if current[0] > config.doubt_timeout:
            self.watch.display.add_doubt_timeout(0, played_time, current)
            logging.info(f'no challenge possible, because of timeout {current[0]}')
        else:
            self.watch.display.add_remove_tiles(0, played_time, current)  # player 1 has to remove the last move
            self.last_submit = pool.submit(valid_challenge, self.last_submit, self.game, 0,
                                           (played_time[0], played_time[1]), self.op_event)
            LED.switch_on({LEDEnum.yellow})  # turn on LED green (blink), yellow
            LED.blink_on({LEDEnum.green}, switch_off=False)
        return P0

    def do_valid_challenge1(self) -> str:
        """player 1 has a valid challenge for the last move from player 0"""
        logging.info(f'{self.current_state} - (valid challenge) -> {P1}')
        _, played_time, current = self.watch.status()
        if current[1] > config.doubt_timeout:
            self.watch.display.add_doubt_timeout(1, played_time, current)
            logging.info(f'no challenge possible, because of timeout {current[1]}')
        else:
            self.watch.display.add_remove_tiles(1, played_time, current)  # player 0 has to remove the last move
            self.last_submit = pool.submit(valid_challenge, self.last_submit, self.game, 1,
                                           (played_time[0], played_time[1]), self.op_event)
            LED.switch_on({LEDEnum.yellow})  # turn on LED red (blink), yellow
            LED.blink_on({LEDEnum.red}, switch_off=False)
        return P1

    def do_invalid_challenge0(self) -> str:
        """player 0 has an invalid challenge for the last move from player 1"""
        logging.info(
            f'{self.current_state} - (invalid challenge) -> {P0} (-{config.malus_doubt:2d})')  # -10
        _, played_time, current = self.watch.status()
        if current[0] > config.doubt_timeout:
            self.watch.display.add_doubt_timeout(0, played_time, current)
            logging.info(f'no challenge possible, because of timeout {current[0]}')
        else:
            self.watch.display.add_malus(0, played_time, current)  # player 0 gets a malus
            self.last_submit = pool.submit(invalid_challenge, self.last_submit, self.game, 0,
                                           (played_time[0], played_time[1]), self.op_event)
            LED.switch_on({LEDEnum.yellow})  # turn on LED green (blink), yellow
            LED.blink_on({LEDEnum.green}, switch_off=False)
        return P0

    def do_invalid_challenge1(self) -> str:
        """player 1 has an invalid challenge for the last move from player 0"""
        logging.info(
            f'{self.current_state} - (invalid challenge) -> {P1} (-{config.malus_doubt:2d})')  # -10
        _, played_time, current = self.watch.status()
        if current[1] > config.doubt_timeout:
            self.watch.display.add_doubt_timeout(1, played_time, current)
            logging.info(f'no challenge possible, because of timeout {current[1]}')
        else:
            self.watch.display.add_malus(1, played_time, current)  # player 1 gets a malus
            self.last_submit = pool.submit(invalid_challenge, self.last_submit, self.game, 1,
                                           (played_time[0], played_time[1]), self.op_event)
            LED.switch_on({LEDEnum.yellow})  # turn on LED red (blink), yellow
            LED.blink_on({LEDEnum.red}, switch_off=False)
        return P1

    def do_new_player_names(self, name1: str, name2: str) -> None:
        "set new player names and upload status, if state is START"
        self.game.nicknames = (name1, name2)
        if self.current_state == START:
            store_status(self.game)
            self.do_ready()

    def do_new_game(self) -> str:
        """Starts a new game"""
        LED.switch_on({})  # type: ignore
        self.picture = None
        self.watch.reset()
        self.game.new_game()
        gc.collect()
        start_of_game(self.game)
        return self.do_ready()

    def do_end_of_game(self) -> str:
        """Resets state and game to default"""
        logging.info(f'{self.current_state} - (reset) -> {START}')
        LED.switch_on({})  # type: ignore
        LED.blink_on({LEDEnum.yellow})
        end_of_game(None, self.game)
        self.watch.display.show_end_of_game()
        current_state = EOG
        return current_state

    def do_reboot(self) -> str:  # pragma: no cover
        """Perform a reboot"""
        logging.info(f'{self.current_state} - (reboot) -> {START}')
        self.watch.display.show_boot()  # Display message REBOOT
        LED.switch_on({})  # type: ignore
        end_of_game(self.last_submit, self.game)
        self.watch.display.stop()
        current_state = START
        alarm(1)  # raise alarm for reboot
        return current_state

    def do_accesspoint(self) -> str:  # pragma: no cover
        """Switch to AP Mode"""
        import subprocess

        logging.info(f'{self.current_state} - (switch to AP Mode) -> {START}')
        process1 = subprocess.run(['sudo', '-n', '/usr/sbin/wpa_cli', 'list_networks', '-i', 'wlan0'], check=False,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        wifi_raw = process1.stdout.decode().split(sep='\n')[1:-1]
        wifi_list = [element.split(sep='\t') for element in wifi_raw]
        for elem in wifi_list:
            if elem[1] in ('ScrabScrap', 'ScrabScrapTest'):
                _ = subprocess.call(f'sudo -n /usr/sbin/wpa_cli select_network {elem[0]} -i wlan0', shell=True)
                self.watch.display.show_accesspoint()  # Display message AP Mode
                LED.switch_on({})  # type: ignore
        current_state = START
        return current_state

    def press_button(self, button: str) -> None:
        """process button press

        before sending the next event, press button will wait for self.bounce
        """
        try:
            self.current_state = self.state[(self.current_state, button)](self)
            if not self.op_event.is_set():
                self.op_event.set()
            logging.debug(f'{button}')
        except KeyError:
            logging.info('Key Error - ignore')

    def release_button(self, button: str) -> None:
        """process button release

        sets the release time to self.bounce
        """
        pass

    # START, pause => not supported
    state: dict[tuple[str, str], Callable] = {
        (START, GREEN): do_start1,
        (START, RED): do_start0,
        (START, RESET): do_new_game,
        (START, REBOOT): do_reboot,
        (START, AP): do_accesspoint,
        (S0, GREEN): do_move0,
        (S0, YELLOW): do_pause0,
        (P0, RED): do_resume0,
        (P0, YELLOW): do_resume0,
        (P0, DOUBT0): do_valid_challenge0,
        (P0, DOUBT1): do_invalid_challenge0,
        (P0, RESET): do_end_of_game,
        (P0, REBOOT): do_reboot,
        (P0, AP): do_accesspoint,
        (S1, RED): do_move1,
        (S1, YELLOW): do_pause1,
        (P1, GREEN): do_resume1,
        (P1, YELLOW): do_resume1,
        (P1, DOUBT1): do_valid_challenge1,
        (P1, DOUBT0): do_invalid_challenge1,
        (P1, RESET): do_end_of_game,
        (P1, REBOOT): do_reboot,
        (P1, AP): do_accesspoint,
        (EOG, GREEN): do_new_game,
        (EOG, RED): do_new_game,
        (EOG, YELLOW): do_new_game,
        (EOG, REBOOT): do_reboot,
        (EOG, AP): do_accesspoint
    }
