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
# pylint: disable=too-many-public-methods

import gc
import logging
import threading
from concurrent.futures import Future
from signal import alarm
from time import sleep
from typing import Callable, Optional, Tuple

from config import config
from hardware import camera
from hardware.button import Button
from hardware.led import LED, LEDEnum
from processing import (
    admin_change_move,
    admin_change_score,
    admin_del_challenge,
    admin_ins_challenge,
    admin_insert_moves,
    admin_toggle_challenge_type,
    check_resume,
    end_of_game,
    event_set,
    invalid_challenge,
    move,
    remove_blanko,
    set_blankos,
    start_of_game,
    store_game_status,
    store_zip_from_game,
    valid_challenge,
    waitfor_future,
)
from scrabble import Game, MoveType
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
    last_submit: Optional[Future] = None  # last submit to thread pool; waiting for processing of the last move
    game: Game = Game(None)
    picture = None
    op_event = threading.Event()
    ap_mode = False

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
        cls.current_state = START
        return cls.current_state

    @classmethod
    def do_start(cls, player: int) -> str:
        """Start playing with player 0/1"""
        next_state = (S0, S1)[player]
        next_led = ({LEDEnum.green}, {LEDEnum.red})[player]
        logging.info(f'{cls.current_state} - (start) -> {next_state}')
        ScrabbleWatch.start(player)
        LED.switch_on(next_led)  # turn on LED red
        ScrabbleWatch.display.render_display(0, (0, 0), (0, 0))
        ScrabbleWatch.display.render_display(1, (0, 0), (0, 0))
        return next_state

    @classmethod
    def do_move(cls, player: int) -> str:
        """analyze players 0/1 move"""
        next_player = abs(player - 1)
        next_state = (S0, S1)[next_player]
        next_led = ({LEDEnum.green}, {LEDEnum.red})[next_player]
        logging.info(f'{cls.current_state} - (move) -> {next_state}')
        _, (time0, time1), _ = ScrabbleWatch.status()
        ScrabbleWatch.start(next_player)
        LED.switch_on(next_led)  # turn on next player LED
        cls.picture = camera.cam.read().copy()
        cls.last_submit = pool.submit(move, cls.last_submit, cls.game, cls.picture, player, (time0, time1), cls.op_event)
        return next_state

    @classmethod
    def do_pause(cls, player: int) -> str:
        """pause pressed while player 0 is active"""
        next_state = (P0, P1)[player]
        next_led = ({LEDEnum.green, LEDEnum.yellow}, {LEDEnum.red, LEDEnum.yellow})[player]
        logging.info(f'{cls.current_state} - (pause) -> {next_state}')
        ScrabbleWatch.pause()
        LED.switch_on(next_led)  # turn on player pause LED
        return next_state

    @classmethod
    def do_resume(cls, player: int) -> str:
        """resume from pause while player 0 is active"""
        next_state = (S0, S1)[player]
        next_led = ({LEDEnum.green}, {LEDEnum.red})[player]
        logging.info(f'{cls.current_state} - (resume) -> {next_state}')
        _, (time0, time1), current_time = ScrabbleWatch.status()
        ScrabbleWatch.resume()
        LED.switch_on(next_led)  # turn on player LED
        cls.picture = camera.cam.read(peek=True).copy()
        cls.last_submit = pool.submit(
            check_resume, cls.last_submit, cls.game, cls.picture, player, (time0, time1), current_time, cls.op_event
        )
        return next_state

    @classmethod
    def do_valid_challenge(cls, player: int) -> str:
        """player 0/1 has a valid challenge for the last move from player 1/0"""
        next_state = (P0, P1)[player]
        logging.info(f'{cls.current_state} - (valid challenge) -> {next_state}')
        _, played_time, current = ScrabbleWatch.status()
        if current[player] > config.doubt_timeout:
            ScrabbleWatch.display.add_doubt_timeout(player, played_time, current)
            logging.warning(f'valid challenge after timeout {current[0]}')
        ScrabbleWatch.display.add_remove_tiles(player, played_time, current)  # player 1 has to remove the last move
        cls.last_submit = pool.submit(
            valid_challenge, cls.last_submit, cls.game, player, (played_time[0], played_time[1]), cls.op_event
        )
        LED.switch_on({LEDEnum.yellow})  # turn on player LED (blink), yellow
        LED.blink_on(({LEDEnum.green}, {LEDEnum.red})[player], switch_off=False)
        return next_state

    @classmethod
    def do_invalid_challenge(cls, player: int) -> str:
        """player 0/1 has an invalid challenge for the last move from player 1/0"""
        next_state = (P0, P1)[player]
        logging.info(f'{cls.current_state} - (invalid challenge) -> {next_state} (-{config.malus_doubt:2d})')  # -10
        _, played_time, current = ScrabbleWatch.status()
        if current[player] > config.doubt_timeout:
            ScrabbleWatch.display.add_doubt_timeout(player, played_time, current)
            logging.warning(f'invalid challenge after timeout {current[player]}')
        ScrabbleWatch.display.add_malus(player, played_time, current)  # player 0 gets a malus
        cls.last_submit = pool.submit(
            invalid_challenge, cls.last_submit, cls.game, player, (played_time[0], played_time[1]), cls.op_event
        )
        LED.switch_on({LEDEnum.yellow})  # turn on player LED (blink), yellow
        LED.blink_on(({LEDEnum.green}, {LEDEnum.red})[player], switch_off=False)
        return next_state

    @classmethod
    def do_new_player_names(cls, name1: str, name2: str) -> None:
        """set new player names and upload status, if state is START"""
        cls.game.nicknames = (name1, name2)
        if cls.current_state == START:
            store_game_status(cls.game)
            cls.do_ready()
        event_set(cls.op_event)

    @classmethod
    def do_set_blankos(cls, coord: str, value: str):
        """set char for blanko"""
        cls.last_submit = pool.submit(set_blankos, cls.last_submit, cls.game, coord, value, cls.op_event)
        waitfor_future(cls.last_submit)

    @classmethod
    def do_remove_blanko(cls, coord: str):
        """remove blanko"""
        cls.last_submit = pool.submit(remove_blanko, cls.last_submit, cls.game, coord, cls.op_event)
        waitfor_future(cls.last_submit)

    @classmethod
    def do_insert_moves(cls, move_number: int):
        """insert two exchange move before move number via api"""
        cls.last_submit = pool.submit(admin_insert_moves, cls.last_submit, cls.game, move_number, cls.op_event)
        waitfor_future(cls.last_submit)

    @classmethod
    def do_edit_move(cls, move_number: int, coord: Tuple[int, int], isvertical: bool, word: str):
        """change move via api"""
        cls.last_submit = pool.submit(
            admin_change_move, cls.last_submit, cls.game, move_number, coord, isvertical, word, cls.op_event
        )
        waitfor_future(cls.last_submit)

    @classmethod
    def do_change_score(cls, move_number: int, score: Tuple[int, int]):
        """change scoring value"""
        cls.last_submit = pool.submit(admin_change_score, cls.last_submit, cls.game, move_number, score, cls.op_event)
        waitfor_future(cls.last_submit)

    @classmethod
    def do_del_challenge(cls, move_number: int):
        """delete challenge with move number via api"""
        cls.last_submit = pool.submit(admin_del_challenge, cls.last_submit, cls.game, move_number, cls.op_event)
        waitfor_future(cls.last_submit)

    @classmethod
    def do_toggle_challenge_type(cls, move_number: int):
        """delete challenge with move number via api"""
        cls.last_submit = pool.submit(admin_toggle_challenge_type, cls.last_submit, cls.game, move_number, cls.op_event)
        waitfor_future(cls.last_submit)

    @classmethod
    def do_ins_challenge(cls, move_number: int):
        """insert invalid challenge for move_number via api"""
        cls.last_submit = pool.submit(
            admin_ins_challenge, cls.last_submit, cls.game, move_number, MoveType.CHALLENGE_BONUS, cls.op_event
        )
        waitfor_future(cls.last_submit)

    @classmethod
    def do_ins_withdraw(cls, move_number: int):
        """insert withdraw for move_number via api"""
        cls.last_submit = pool.submit(
            admin_ins_challenge, cls.last_submit, cls.game, move_number, MoveType.WITHDRAW, cls.op_event
        )
        waitfor_future(cls.last_submit)

    @classmethod
    def do_new_game(cls) -> str:
        """Starts a new game"""
        from contextlib import suppress

        with suppress(Exception):
            cls.current_state = BLOCKING
            LED.switch_on({LEDEnum.green, LEDEnum.red})
            cls.picture = None
            ScrabbleWatch.reset()
            cls.game.new_game()
            gc.collect()

        start_of_game(cls.game)
        event_set(cls.op_event)
        return cls.do_ready()

    @classmethod
    def do_end_of_game(cls) -> str:
        """Resets state and game to default"""
        from contextlib import suppress

        logging.info(f'{cls.current_state} - (reset) -> {START}')
        cls.current_state = BLOCKING
        LED.switch_on(set())
        ScrabbleWatch.display.show_ready(('end of', 'game'))
        with suppress(Exception):
            end_of_game(None, cls.game, cls.op_event)
        with suppress(Exception):
            store_zip_from_game(cls.game)
        with suppress(Exception):
            ScrabbleWatch.display.show_end_of_game()
        LED.blink_on({LEDEnum.yellow})
        cls.current_state = EOG
        return EOG

    @classmethod
    def do_reboot(cls) -> str:  # pragma: no cover
        """Perform a reboot"""
        from contextlib import suppress

        logging.info(f'{cls.current_state} - (reboot) -> {START}')
        cls.current_state = BLOCKING
        with suppress(Exception):
            ScrabbleWatch.display.show_boot()  # Display message REBOOT
            LED.switch_on(set())
            end_of_game(cls.last_submit, cls.game)
        with suppress(Exception):
            store_zip_from_game(cls.game)
        ScrabbleWatch.display.stop()
        current_state = START
        alarm(1)  # raise alarm for reboot
        return current_state

    # pylint: disable=duplicate-code
    @classmethod
    def do_accesspoint(cls) -> str:  # pragma: no cover
        """Switch to AP Mode"""
        import subprocess

        ScrabbleWatch.display.show_ready(('switch', 'AP'))
        cls.ap_mode = not cls.ap_mode
        logging.info(f'{cls.current_state} - (switch to AP Mode) -> {AP}')
        cmd = ['sudo', '-n', '/usr/bin/nmcli', 'connection', 'up' if cls.ap_mode else 'down', 'ScrabScrap']
        logging.debug(f'switch to AP {cmd=}')
        ret = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if ret.returncode == 0:
            if cls.ap_mode:
                LED.switch_on(set())
                sleep(5)
                ScrabbleWatch.display.show_accesspoint()  # Display message AP Mode
            else:
                sleep(5)
                LED.switch_on({LEDEnum.green, LEDEnum.red})
                ScrabbleWatch.display.show_ready()

        current_state = START
        return current_state

    @classmethod
    def press_button(cls, button: str) -> None:
        """process button press

        before sending the next event, press button will wait for self.bounce
        """
        try:
            try:
                cls.current_state = cls.state[(cls.current_state, button)]()
            except Exception as oops:  # pylint: disable=broad-exception-caught
                logging.warning(f'ignore invalid exception on button handling {oops}')
            event_set(cls.op_event)
            logging.info(f'{button}')
        except KeyError:
            logging.warning('Key Error - ignore')

    # unused:
    # @classmethod
    # def release_button(cls, button: str) -> None:
    #     """process button release
    #     sets the release time to self.bounce
    #     """
    #     pass

    # START, pause => not supported
    # pylint: disable=unnecessary-lambda
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
        (EOG, AP): lambda: State.do_accesspoint(),
    }
