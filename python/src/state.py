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
from signal import alarm
from time import sleep
from typing import Callable

from config import config
from hardware import camera
from hardware.button import Button
from hardware.led import LED, LEDEnum
from processing import (
    check_resume,
    end_of_game,
    event_set,
    invalid_challenge,
    move,
    start_of_game,
    store_zip_from_game,
    valid_challenge,
    write_files,
)
from scrabble import Game
from scrabblewatch import ScrabbleWatch
from threadpool import command_queue
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
    def do_ready(cls, next_state: str = START) -> str:
        """Game can be started"""
        logging.debug(f'{cls.game.nicknames}')
        ScrabbleWatch.display.show_ready(cls.game.nicknames)
        ScrabbleWatch.display.set_game(cls.game)
        cls.current_state = next_state
        return cls.current_state

    @classmethod
    def do_start(cls, player: int, next_state: str) -> str:
        """Start playing with player 0/1"""
        next_led = ({LEDEnum.green}, {LEDEnum.red})[player]
        logging.info(f'{cls.current_state} - (start) -> {next_state}')
        ScrabbleWatch.start(player)
        LED.switch_on(next_led)  # turn on LED red
        ScrabbleWatch.display.render_display(0, (0, 0), (0, 0))
        ScrabbleWatch.display.render_display(1, (0, 0), (0, 0))
        return next_state

    @classmethod
    def do_move(cls, player: int, next_state: str) -> str:
        """analyze players 0/1 move"""
        next_player = abs(player - 1)
        next_led = ({LEDEnum.green}, {LEDEnum.red})[next_player]
        logging.info(f'{cls.current_state} - (move) -> {next_state}')
        _, (time0, time1), _ = ScrabbleWatch.status()
        ScrabbleWatch.start(next_player)
        LED.switch_on(next_led)  # turn on next player LED
        cls.picture = camera.cam.read().copy()
        command_queue.put(move(cls.game, cls.picture, player, (time0, time1), cls.op_event))
        return next_state

    @classmethod
    def do_pause(cls, next_state: str) -> str:
        """pause pressed while player 0 is active"""
        logging.info(f'{cls.current_state} - (pause) -> {next_state}')
        ScrabbleWatch.pause()
        LED.switch_on({LEDEnum.yellow})  # turn on player pause LED
        return next_state

    @classmethod
    def do_resume(cls, player: int, next_state: str) -> str:
        """resume from pause while player 0 is active"""
        next_led = ({LEDEnum.green}, {LEDEnum.red})[player]
        logging.info(f'{cls.current_state} - (resume) -> {next_state}')
        _, (time0, time1), current_time = ScrabbleWatch.status()
        ScrabbleWatch.resume()
        LED.switch_on(next_led)  # turn on player LED
        cls.picture = camera.cam.read(peek=True).copy()
        command_queue.put(check_resume(cls.game, cls.picture, player, (time0, time1), current_time, cls.op_event))
        return next_state

    @classmethod
    def do_valid_challenge(cls, player: int, next_state: str) -> str:
        """player 0/1 has a valid challenge for the last move from player 1/0"""
        logging.info(f'{cls.current_state} - (valid challenge) -> {next_state}')
        _, played_time, current = ScrabbleWatch.status()
        if current[player] > config.scrabble.doubt_timeout:
            ScrabbleWatch.display.add_doubt_timeout(player, played_time, current)
            logging.warning(f'valid challenge after timeout {current[0]}')
        ScrabbleWatch.display.add_remove_tiles(player, played_time, current)  # player 1 has to remove the last move
        command_queue.put(valid_challenge(cls.game, player, (played_time[0], played_time[1]), cls.op_event))
        LED.switch_on({LEDEnum.yellow})  # turn on player LED (blink), yellow
        LED.blink_on(({LEDEnum.green}, {LEDEnum.red})[player], switch_off=False)
        return next_state

    @classmethod
    def do_invalid_challenge(cls, player: int, next_state: str) -> str:
        """player 0/1 has an invalid challenge for the last move from player 1/0"""
        logging.info(f'{cls.current_state} - (invalid challenge) -> {next_state} (-{config.scrabble.malus_doubt:2d})')  # -10
        _, played_time, current = ScrabbleWatch.status()
        if current[player] > config.scrabble.doubt_timeout:
            ScrabbleWatch.display.add_doubt_timeout(player, played_time, current)
            logging.warning(f'invalid challenge after timeout {current[player]}')
        ScrabbleWatch.display.add_malus(player, played_time, current)  # player 0 gets a malus
        command_queue.put(invalid_challenge(cls.game, player, (played_time[0], played_time[1]), cls.op_event))
        LED.switch_on({LEDEnum.yellow})  # turn on player LED (blink), yellow
        LED.blink_on(({LEDEnum.green}, {LEDEnum.red})[player], switch_off=False)
        return next_state

    @classmethod
    def do_new_player_names(cls, name1: str, name2: str) -> None:
        """set new player names"""
        cls.game.nicknames = (name1, name2)
        if cls.current_state == START:
            cls.do_ready()
        write_files(cls.game)
        event_set(cls.op_event)

    @classmethod
    def do_new_game(cls, next_state: str = START) -> str:
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
        return cls.do_ready(next_state=next_state)

    @classmethod
    def do_end_of_game(cls, next_state: str = EOG) -> str:
        """Resets state and game to default"""
        from contextlib import suppress

        logging.info(f'{cls.current_state} - (reset) -> {next_state}')
        cls.current_state = BLOCKING
        LED.switch_on(set())
        ScrabbleWatch.display.show_ready(('end of', 'game'))
        with suppress(Exception):
            command_queue.put(end_of_game(cls.game))
        with suppress(Exception):
            store_zip_from_game(cls.game)
        # command_queue.put(None)
        # command_queue.join()
        with suppress(Exception):
            ScrabbleWatch.display.show_end_of_game()
        LED.blink_on({LEDEnum.yellow})
        event_set(cls.op_event)
        cls.current_state = next_state
        return cls.current_state

    @classmethod
    def do_reboot(cls) -> str:  # pragma: no cover
        """Perform a reboot"""
        from contextlib import suppress

        logging.info(f'{cls.current_state} - (reboot) -> {START}')
        cls.current_state = BLOCKING
        with suppress(Exception):
            ScrabbleWatch.display.show_boot()  # Display message REBOOT
            LED.switch_on(set())
            end_of_game(cls.game)
        with suppress(Exception):
            store_zip_from_game(cls.game)
        ScrabbleWatch.display.stop()
        cls.current_state = START
        alarm(1)  # raise alarm for reboot
        return cls.current_state

    # pylint: disable=duplicate-code
    @classmethod
    def do_accesspoint(cls, next_state: str = START) -> str:  # pragma: no cover
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
        cls.current_state = next_state
        return cls.current_state

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
        (START, GREEN): lambda: State.do_start(player=1, next_state=S1),
        (START, RED): lambda: State.do_start(player=0, next_state=S0),
        (START, RESET): lambda: State.do_new_game(next_state=START),
        (START, REBOOT): lambda: State.do_reboot(),
        (START, AP): lambda: State.do_accesspoint(next_state=START),
        (S0, GREEN): lambda: State.do_move(player=0, next_state=S1),
        (S0, YELLOW): lambda: State.do_pause(next_state=P0),
        (P0, RED): lambda: State.do_resume(player=0, next_state=S0),
        (P0, YELLOW): lambda: State.do_resume(player=0, next_state=S0),
        (P0, DOUBT0): lambda: State.do_valid_challenge(player=0, next_state=P0),
        (P0, DOUBT1): lambda: State.do_invalid_challenge(player=0, next_state=P0),
        (P0, RESET): lambda: State.do_end_of_game(next_state=EOG),
        (P0, REBOOT): lambda: State.do_reboot(),
        (S1, RED): lambda: State.do_move(player=1, next_state=S0),
        (S1, YELLOW): lambda: State.do_pause(next_state=P1),
        (P1, GREEN): lambda: State.do_resume(player=1, next_state=S1),
        (P1, YELLOW): lambda: State.do_resume(player=1, next_state=S1),
        (P1, DOUBT1): lambda: State.do_valid_challenge(player=1, next_state=P1),
        (P1, DOUBT0): lambda: State.do_invalid_challenge(player=1, next_state=P1),
        (P1, RESET): lambda: State.do_end_of_game(next_state=EOG),
        (P1, REBOOT): lambda: State.do_reboot(),
        (EOG, GREEN): lambda: State.do_new_game(next_state=START),
        (EOG, RED): lambda: State.do_new_game(next_state=START),
        (EOG, YELLOW): lambda: State.do_new_game(next_state=START),
        (EOG, REBOOT): lambda: State.do_reboot(),
        (EOG, AP): lambda: State.do_accesspoint(next_state=START),
    }
