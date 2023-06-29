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
from concurrent import futures
from concurrent.futures import Future
from signal import alarm
from time import sleep
from typing import Callable, Optional, Tuple

from config import Config
from hardware.button import Button
from hardware.camera_thread import Camera
from hardware.led import LED, LEDEnum
from processing import (end_of_game, invalid_challenge, move, start_of_game,
                        store_status, store_zip_from_game, valid_challenge)
from scrabble import Game
from scrabblewatch import ScrabbleWatch
from threadpool import pool
from util import Static

# states
START = 'START'
S0 = 'S0'
S1 = 'S1'
P0 = 'P0'
P1 = 'P1'
EOG = 'EOG'  # end of game
BLOCKING = 'BLOCK'  # ignore button press

# buttons
GREEN = 'GREEN'
YELLOW = 'YELLOW'
RED = 'RED'
DOUBT0 = 'DOUBT0'
DOUBT1 = 'DOUBT1'
RESET = 'RESET'
REBOOT = 'REBOOT'
AP = 'AP'


class State(Static):
    """State machine of the scrabble game"""
    current_state: str = START
    button_handler = Button
    cam: Optional[Camera] = None
    last_submit: Optional[Future] = None  # last submit to thread pool; waiting for processing of the last move
    game: Game = Game(None)
    picture = None
    op_event = threading.Event()

    # def __init__(self, cam=None, watch: Optional[ScrabbleWatch] = None, button_handler: Optional[Button] = None) -> None:
    #     self.current_state: str = START
    #     self.watch: ScrabbleWatch = watch if watch else ScrabbleWatch()
    #     self.button_handler: Button = button_handler if button_handler else Button()
    #     self.cam = cam
    #     self.last_submit: Optional[Future] = None  # last submit to thread pool; waiting for processing of the last move
    #     self.game: Game = Game(None)
    #     self.picture = None
    #     self.op_event = threading.Event()

    @classmethod
    def init(cls) -> None:
        """init state machine"""
        cls.button_handler.start(func_pressed=cls.press_button)
        cls.do_new_game()

    @classmethod
    def do_ready(cls) -> str:
        """Game can be started"""
        logging.debug(f'{cls.game.nicknames}')
        ScrabbleWatch.display.show_ready(cls.game.nicknames)
        ScrabbleWatch.display.set_game(cls.game)
        cls.picture = cls.cam.read(peek=True) if cls.cam else None  # type: ignore
        cls.current_state = START
        return cls.current_state

    @classmethod
    def do_start(cls, player: int) -> str:
        """Start playing with player 0/1"""
        assert player in [0, 1], "invalid player number"

        next_state = (S0, S1)[player]
        next_led = ({LEDEnum.green}, {LEDEnum.red})[player]
        logging.info(f'{cls.current_state} - (start) -> {next_state}')
        ScrabbleWatch.start(player)
        LED.switch_on(next_led)  # turn on LED red
        ScrabbleWatch.display.render_display(0, [0, 0], [0, 0])
        return next_state

    @classmethod
    def do_move(cls, player: int) -> str:
        """analyze players 0/1 move"""
        assert player in [0, 1], "invalid player number"

        next_player = abs(player - 1)
        next_state = (S0, S1)[next_player]
        next_led = ({LEDEnum.green}, {LEDEnum.red})[next_player]
        logging.info(f'{cls.current_state} - (move) -> {next_state}')
        _, (time0, time1), _ = ScrabbleWatch.status()
        ScrabbleWatch.start(next_player)
        LED.switch_on(next_led)  # turn on next player LED
        cls.picture = cls.cam.read()  # type: ignore
        cls.last_submit = pool.submit(move, cls.last_submit, cls.game, cls.picture, player, (time0, time1), cls.op_event)
        return next_state

    @classmethod
    def do_pause(cls, player: int) -> str:
        """pause pressed while player 0 is active"""
        assert player in [0, 1], "invalid player number"

        next_state = (P0, P1)[player]
        next_led = ({LEDEnum.green, LEDEnum.yellow}, {LEDEnum.red, LEDEnum.yellow})[player]
        logging.info(f'{cls.current_state} - (pause) -> {next_state}')
        ScrabbleWatch.pause()
        LED.switch_on(next_led)  # turn on player pause LED
        return next_state

    @classmethod
    def do_resume(cls, player: int) -> str:
        """resume from pause while player 0 is active"""
        assert player in [0, 1], "invalid player number"

        next_state = (S0, S1)[player]
        next_led = ({LEDEnum.green}, {LEDEnum.red})[player]
        logging.info(f'{cls.current_state} - (resume) -> {next_state}')
        ScrabbleWatch.resume()
        LED.switch_on(next_led)  # turn on player LED
        return next_state

    @classmethod
    def do_valid_challenge(cls, player: int) -> str:
        """player 0/1 has a valid challenge for the last move from player 1/0"""
        assert player in [0, 1], "invalid player number"

        next_state = (P0, P1)[player]
        logging.info(f'{cls.current_state} - (valid challenge) -> {next_state}')
        _, played_time, current = ScrabbleWatch.status()
        if current[player] > Config.doubt_timeout():
            ScrabbleWatch.display.add_doubt_timeout(player, played_time, current)
            logging.info(f'no challenge possible, because of timeout {current[0]}')
        else:
            ScrabbleWatch.display.add_remove_tiles(player, played_time, current)  # player 1 has to remove the last move
            cls.last_submit = pool.submit(valid_challenge, cls.last_submit, cls.game, player,
                                          (played_time[0], played_time[1]), cls.op_event)
            LED.switch_on({LEDEnum.yellow})  # turn on player LED (blink), yellow
            led_on = ({LEDEnum.green}, {LEDEnum.red})[player]
            LED.blink_on(led_on, switch_off=False)
        return next_state

    @classmethod
    def do_invalid_challenge(cls, player: int) -> str:
        """player 0/1 has an invalid challenge for the last move from player 1/0"""
        assert player in [0, 1], "invalid player number"

        next_state = (P0, P1)[player]
        logging.info(
            f'{cls.current_state} - (invalid challenge) -> {next_state} (-{Config.malus_doubt():2d})')  # -10
        _, played_time, current = ScrabbleWatch.status()
        if current[player] > Config.doubt_timeout():
            ScrabbleWatch.display.add_doubt_timeout(player, played_time, current)
            logging.info(f'no challenge possible, because of timeout {current[player]}')
        else:
            ScrabbleWatch.display.add_malus(player, played_time, current)  # player 0 gets a malus
            cls.last_submit = pool.submit(invalid_challenge, cls.last_submit, cls.game, player,
                                          (played_time[0], played_time[1]), cls.op_event)
            LED.switch_on({LEDEnum.yellow})  # turn on player LED (blink), yellow
            led_on = ({LEDEnum.green}, {LEDEnum.red})[player]
            LED.blink_on(led_on, switch_off=False)
        return next_state

    @classmethod
    def do_new_player_names(cls, name1: str, name2: str) -> None:
        "set new player names and upload status, if state is START"
        cls.game.nicknames = (name1, name2)
        if cls.current_state == START:
            store_status(cls.game)
            cls.do_ready()
        if not cls.op_event.is_set():
            cls.op_event.set()

    @classmethod
    def do_set_blankos(cls, coord: str, value: str):
        """set char for blanko"""
        from processing import set_blankos
        cls.last_submit = pool.submit(set_blankos, cls.last_submit, cls.game, coord, value, cls.op_event)
        _, not_done = futures.wait({cls.last_submit})
        assert len(not_done) == 0, 'error while waiting for future'

    @classmethod
    def do_insert_moves(cls, move_number: int):
        """insert two exchange move before move number via api"""
        from processing import admin_insert_moves
        cls.last_submit = pool.submit(admin_insert_moves, cls.last_submit, cls.game, move_number, cls.op_event)
        _, not_done = futures.wait({cls.last_submit})
        assert len(not_done) == 0, 'error while waiting for future'

    @classmethod
    def do_edit_move(cls, move_number: int, coord: Tuple[int, int], isvertical: bool, word: str):
        """change move via api"""
        from processing import admin_change_move
        cls.last_submit = pool.submit(admin_change_move, cls.last_submit, cls.game, move_number, coord, isvertical,
                                      word, cls.op_event)
        _, not_done = futures.wait({cls.last_submit})
        assert len(not_done) == 0, 'error while waiting for future'

    @classmethod
    def do_change_score(cls, move_number: int, score: Tuple[int, int]):
        """change scoring value"""
        from processing import admin_change_score
        cls.last_submit = pool.submit(admin_change_score, cls.last_submit, cls.game, move_number, score, cls.op_event)
        _, not_done = futures.wait({cls.last_submit})
        assert len(not_done) == 0, 'error while waiting for future'

    @classmethod
    def do_new_game(cls) -> str:
        """Starts a new game"""
        from contextlib import suppress

        with suppress(Exception):
            cls.current_state = BLOCKING
            LED.switch_on({})  # type: ignore
            cls.picture = None
            ScrabbleWatch.reset()
            cls.game.new_game()
            gc.collect()
        start_of_game(cls.game)
        if not cls.op_event.is_set():
            cls.op_event.set()
        return cls.do_ready()

    @classmethod
    def do_end_of_game(cls) -> str:
        """Resets state and game to default"""
        from contextlib import suppress

        logging.info(f'{cls.current_state} - (reset) -> {START}')
        with suppress(Exception):
            cls.current_state = BLOCKING
            LED.switch_on({})  # type: ignore
            ScrabbleWatch.display.show_ready(('prepare', 'end'))
            end_of_game(None, cls.game, cls.op_event)

        ScrabbleWatch.display.show_end_of_game()

        with suppress(Exception):
            store_zip_from_game(cls.game)
        LED.blink_on({LEDEnum.yellow})
        return EOG

    @classmethod
    def do_reboot(cls) -> str:  # pragma: no cover
        """Perform a reboot"""
        from contextlib import suppress

        logging.info(f'{cls.current_state} - (reboot) -> {START}')
        with suppress(Exception):
            cls.current_state = BLOCKING
            ScrabbleWatch.display.show_boot()  # Display message REBOOT
            LED.switch_on({})  # type: ignore
            end_of_game(cls.last_submit, cls.game)
            store_zip_from_game(cls.game)
        ScrabbleWatch.display.stop()
        current_state = START
        alarm(1)  # raise alarm for reboot
        return current_state

    @classmethod
    def do_accesspoint(cls) -> str:  # pragma: no cover
        """Switch to AP Mode"""
        import subprocess

        logging.info(f'{cls.current_state} - (switch to AP Mode) -> {START}')
        process1 = subprocess.run(['sudo', '-n', '/usr/sbin/wpa_cli', 'list_networks', '-i', 'wlan0'], check=False,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        wifi_raw = process1.stdout.decode().split(sep='\n')[1:-1]
        wifi_list = [element.split(sep='\t') for element in wifi_raw]
        for elem in wifi_list:
            if elem[1] in ('ScrabScrap', 'ScrabScrapTest'):
                _ = subprocess.call(f'sudo -n /usr/sbin/wpa_cli select_network {elem[0]} -i wlan0', shell=True)
                ScrabbleWatch.display.show_accesspoint()  # Display message AP Mode
                LED.switch_on({})  # type: ignore
                sleep(5)
                ScrabbleWatch.display.show_accesspoint()  # Display message AP Mode
        current_state = START
        return current_state

    @classmethod
    def press_button(cls, button: str) -> None:
        """process button press

        before sending the next event, press button will wait for self.bounce
        """
        try:
            cls.current_state = cls.state[(cls.current_state, button)]()
            if not cls.op_event.is_set():
                cls.op_event.set()
            logging.debug(f'{button}')
        except KeyError:
            logging.info('Key Error - ignore')

    @classmethod
    def release_button(cls, button: str) -> None:
        """process button release

        sets the release time to self.bounce
        """
        pass

    # START, pause => not supported
    state: dict[tuple[str, str], Callable] = {
        (START, GREEN): lambda: State.do_start(1),
        (START, RED): lambda: State.do_start(0),
        (START, RESET): lambda: State.do_new_game(),
        (START, REBOOT): lambda: State.do_reboot(),
        (START, AP): lambda: State.do_accesspoint(),
        (S0, GREEN): lambda: State.do_move(0),
        (S0, YELLOW): lambda: State.do_pause(0),
        (P0, RED): lambda: State.do_resume(0),
        (P0, YELLOW): lambda: State.do_resume(0),
        (P0, DOUBT0): lambda: State.do_valid_challenge(0),
        (P0, DOUBT1): lambda: State.do_invalid_challenge(0),
        (P0, RESET): lambda: State.do_end_of_game(),
        (P0, REBOOT): lambda: State.do_reboot(),
        (P0, AP): lambda: State.do_accesspoint(),
        (S1, RED): lambda: State.do_move(1),
        (S1, YELLOW): lambda: State.do_pause(1),
        (P1, GREEN): lambda: State.do_resume(1),
        (P1, YELLOW): lambda: State.do_resume(1),
        (P1, DOUBT1): lambda: State.do_valid_challenge(1),
        (P1, DOUBT0): lambda: State.do_invalid_challenge(1),
        (P1, RESET): lambda: State.do_end_of_game(),
        (P1, REBOOT): lambda: State.do_reboot(),
        (P1, AP): lambda: State.do_accesspoint(),
        (EOG, GREEN): lambda: State.do_new_game(),
        (EOG, RED): lambda: State.do_new_game(),
        (EOG, YELLOW): lambda: State.do_new_game(),
        (EOG, REBOOT): lambda: State.do_reboot(),
        (EOG, AP): lambda: State.do_accesspoint()
    }
