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

import logging
import threading
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum, auto
from signal import alarm
from time import sleep
from typing import Callable

from config import config
from hardware import camera
from hardware.button import Button, ButtonEnum
from hardware.led import LED, LEDEnum
from processing import check_resume, end_of_game, event_set, invalid_challenge, move, new_game, valid_challenge
from scrabble import Game
from scrabblewatch import ScrabbleWatch
from utils.threadpool import Command, command_queue
from utils.util import Static

logger = logging.getLogger()


class GameState(Enum):
    """Allowed States"""

    START = auto()
    S0 = auto()
    S1 = auto()
    P0 = auto()
    P1 = auto()
    EOG = auto()
    BLOCKING = auto()


PLAYER_LEDS: dict[int, set] = {0: {LEDEnum.green}, 1: {LEDEnum.red}}


@dataclass
class GameContext:
    """State Context"""

    game: Game
    picture: object = None
    ap_mode: bool = False
    op_event = threading.Event()
    current_state: GameState = GameState.START


class State(Static):
    """State machine of the scrabble game"""

    ctx: GameContext = GameContext(game=Game())
    button_handler = Button

    @classmethod
    def init(cls) -> None:
        """init state machine"""
        cls.button_handler.start(func_pressed=cls.press_button)
        cls.do_new_game()

    @classmethod
    def do_ready(cls, next_state: GameState = GameState.START) -> GameState:
        """Game can be started"""
        logger.debug(f'{cls.ctx.game.nicknames}')
        ScrabbleWatch.display.show_ready(cls.ctx.game.nicknames)
        ScrabbleWatch.display.set_game(cls.ctx.game)
        return next_state

    @classmethod
    def do_start(cls, player: int, next_state: GameState) -> GameState:
        """Start playing with player 0/1"""
        ScrabbleWatch.start(player)
        LED.switch(on=PLAYER_LEDS[player])
        ScrabbleWatch.display.render_display(player, (0, 0), (0, 0))
        cls.ctx.picture = camera.cam.read(peek=True)
        return next_state

    @classmethod
    def do_move(cls, player: int, next_state: GameState) -> GameState:
        """analyze players 0/1 move"""
        next_player = abs(player - 1)
        _, played_time, _ = ScrabbleWatch.status()
        ScrabbleWatch.start(next_player)
        LED.switch(on=PLAYER_LEDS[next_player])
        cls.ctx.picture = camera.cam.read()
        with suppress(Exception):
            command_queue.put_nowait(Command(move, cls.ctx.game, cls.ctx.picture, player, played_time, cls.ctx.op_event))
        return next_state

    @classmethod
    def do_pause(cls, next_state: GameState) -> GameState:
        """pause pressed while player 0 is active"""
        ScrabbleWatch.pause()
        LED.switch(on={LEDEnum.yellow})
        return next_state

    @classmethod
    def do_resume(cls, player: int, next_state: GameState) -> GameState:
        """resume from pause while player 0 is active"""
        ScrabbleWatch.resume()
        LED.switch(on=PLAYER_LEDS[player])
        with suppress(Exception):
            cls.ctx.picture = camera.cam.read(peek=True)
            command_queue.put_nowait(Command(check_resume, cls.ctx.game, cls.ctx.picture, cls.ctx.op_event))
        return next_state

    @classmethod
    def do_valid_challenge(cls, player: int, next_state: GameState) -> GameState:
        """player 0/1 has a valid challenge for the last move from player 1/0"""
        _, played_time, current = ScrabbleWatch.status()
        if current[player] > config.scrabble.doubt_timeout:
            ScrabbleWatch.display.add_doubt_timeout(player, played_time, current)
            logger.warning(f'valid challenge after timeout {current[0]}')
        ScrabbleWatch.display.add_remove_tiles(player, played_time, current)  # player 1 has to remove the last move
        with suppress(Exception):
            command_queue.put_nowait(Command(valid_challenge, cls.ctx.game, cls.ctx.op_event))
        LED.switch(on={LEDEnum.yellow}, blink=PLAYER_LEDS[player])
        return next_state

    @classmethod
    def do_invalid_challenge(cls, player: int, next_state: GameState) -> GameState:
        """player 0/1 has an invalid challenge for the last move from player 1/0"""
        _, played_time, current = ScrabbleWatch.status()
        if current[player] > config.scrabble.doubt_timeout:
            ScrabbleWatch.display.add_doubt_timeout(player, played_time, current)
            logger.warning(f'invalid challenge after timeout {current[player]}')
        ScrabbleWatch.display.add_malus(player, played_time, current)  # player 0 gets a malus
        with suppress(Exception):
            command_queue.put_nowait(Command(invalid_challenge, cls.ctx.game, cls.ctx.op_event))
        LED.switch(on={LEDEnum.yellow}, blink=PLAYER_LEDS[player])
        return next_state

    @classmethod
    def do_new_game(cls) -> GameState:
        """Starts a new game"""
        cls.ctx.current_state = GameState.BLOCKING
        LED.switch(on={LEDEnum.green, LEDEnum.red})
        cls.ctx.picture = None
        ScrabbleWatch.reset()
        with suppress(Exception):
            new_game(cls.ctx.game, cls.ctx.op_event)
        ScrabbleWatch.display.set_game(cls.ctx.game)
        ScrabbleWatch.display.show_ready(cls.ctx.game.nicknames)
        cls.ctx.current_state = GameState.START  # method called from outside (api_server)
        return cls.ctx.current_state

    @classmethod
    def do_end_of_game(cls) -> GameState:
        """Resets state and game to default"""
        cls.ctx.current_state = GameState.BLOCKING
        LED.switch()
        ScrabbleWatch.display.show_ready(('end of', 'game'))
        player, _, _ = ScrabbleWatch.status()
        picture = None
        with suppress(Exception):
            picture = camera.cam.read(peek=True)
        with suppress(Exception):
            command_queue.put_nowait(
                Command(end_of_game, game=cls.ctx.game, image=picture, player=player, event=cls.ctx.op_event)
            )
        command_queue.join()  # wait for finishing tasks

        ScrabbleWatch.display.show_end_of_game()
        LED.switch(blink={LEDEnum.yellow})
        cls.ctx.current_state = GameState.EOG  # method called from outside (api_server)
        return cls.ctx.current_state

    @classmethod
    def do_reboot(cls) -> GameState:  # pragma: no cover
        """Perform a reboot"""
        cls.ctx.current_state = GameState.BLOCKING
        ScrabbleWatch.display.show_boot()
        LED.switch()
        with suppress(Exception):
            end_of_game(cls.ctx.game)
        ScrabbleWatch.display.stop()
        cls.ctx.current_state = GameState.START  # method called from outside (api_server)
        alarm(1)  # raise alarm for reboot
        return cls.ctx.current_state

    @classmethod
    def do_accesspoint(cls) -> GameState:  # pragma: no cover
        """Switch to AP Mode"""
        import subprocess

        ScrabbleWatch.display.show_ready(('switch', 'AP'))
        cls.ctx.ap_mode = not cls.ctx.ap_mode
        cmd = ['sudo', '-n', '/usr/bin/nmcli', 'connection', 'up' if cls.ctx.ap_mode else 'down', 'ScrabScrap']
        logger.debug(f'switch to AP {cmd=}')
        ret = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if ret.returncode == 0:
            if cls.ctx.ap_mode:
                LED.switch()
                sleep(5)
                ScrabbleWatch.display.show_accesspoint()
            else:
                sleep(5)
                LED.switch(on={LEDEnum.green, LEDEnum.red})
                ScrabbleWatch.display.show_ready()
        cls.ctx.current_state = GameState.START  # method called from outside (api_server)
        return cls.ctx.current_state

    @classmethod
    def press_button(cls, button: str) -> None:
        """Process button press

        Args:
            button: Button identifier that was pressed
        """
        try:
            logger.debug(f'-> button {button} pressed at {cls.ctx.current_state}')
            # Get state transitions for current state
            state_transitions = cls.transitions.get(cls.ctx.current_state, {})
            # Get specific transition for button
            transition_func = state_transitions.get(ButtonEnum[button])
            if transition_func is None:
                logger.warning(f'Invalid transition: {button} at {cls.ctx.current_state}')
                return
            # Execute transition function and update state
            cls.ctx.current_state = transition_func()
            logger.debug(f'-> new {cls.ctx.current_state}')
        except KeyError:
            logger.warning(f'Key Error: {button} at {cls.ctx.current_state} - ignored')
        except Exception as oops:  # pylint: disable=broad-exception-caught
            logger.warning(f'ignore invalid exception on button handling {oops}')
        event_set(cls.ctx.op_event)

    # unused:
    # @classmethod
    # def release_button(cls, button: str) -> None:
    #     """process button release
    #     sets the release time to self.bounce
    #     """
    #     pass

    # START, pause => not supported
    # pylint: disable=unnecessary-lambda
    transitions: dict[GameState, dict[ButtonEnum, Callable]] = {
        GameState.START: {
            ButtonEnum.GREEN: lambda: State.do_start(player=1, next_state=GameState.S1),
            ButtonEnum.RED: lambda: State.do_start(player=0, next_state=GameState.S0),
            ButtonEnum.RESET: lambda: State.do_new_game(),
            ButtonEnum.REBOOT: lambda: State.do_reboot(),
            ButtonEnum.AP: lambda: State.do_accesspoint(),
        },
        GameState.S0: {
            ButtonEnum.GREEN: lambda: State.do_move(player=0, next_state=GameState.S1),
            ButtonEnum.YELLOW: lambda: State.do_pause(next_state=GameState.P0),
        },
        GameState.P0: {
            ButtonEnum.RED: lambda: State.do_resume(player=0, next_state=GameState.S0),
            ButtonEnum.YELLOW: lambda: State.do_resume(player=0, next_state=GameState.S0),
            ButtonEnum.DOUBT0: lambda: State.do_valid_challenge(player=0, next_state=GameState.P0),
            ButtonEnum.DOUBT1: lambda: State.do_invalid_challenge(player=0, next_state=GameState.P0),
            ButtonEnum.RESET: lambda: State.do_end_of_game(),
            ButtonEnum.REBOOT: lambda: State.do_reboot(),
        },
        GameState.S1: {
            ButtonEnum.RED: lambda: State.do_move(player=1, next_state=GameState.S0),
            ButtonEnum.YELLOW: lambda: State.do_pause(next_state=GameState.P1),
        },
        GameState.P1: {
            ButtonEnum.GREEN: lambda: State.do_resume(player=1, next_state=GameState.S1),
            ButtonEnum.YELLOW: lambda: State.do_resume(player=1, next_state=GameState.S1),
            ButtonEnum.DOUBT0: lambda: State.do_invalid_challenge(player=1, next_state=GameState.P1),
            ButtonEnum.DOUBT1: lambda: State.do_valid_challenge(player=1, next_state=GameState.P1),
            ButtonEnum.RESET: lambda: State.do_end_of_game(),
            ButtonEnum.REBOOT: lambda: State.do_reboot(),
        },
        GameState.EOG: {
            ButtonEnum.GREEN: lambda: State.do_new_game(),
            ButtonEnum.RED: lambda: State.do_new_game(),
            ButtonEnum.YELLOW: lambda: State.do_new_game(),
            ButtonEnum.REBOOT: lambda: State.do_reboot(),
            ButtonEnum.AP: lambda: State.do_accesspoint(),
        },
    }
