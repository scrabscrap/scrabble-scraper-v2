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
from typing import Callable

import cv2

from config import config
from led import LED, LEDEnum
from scrabblewatch import ScrabbleWatch
from threadvideo import video_thread as vt

current_state: str = 'START'
watch: ScrabbleWatch = ScrabbleWatch()


def do_ready() -> str:
    watch.display.show_ready()
    current_state = 'START'
    return current_state


def do_start0() -> str:
    logging.debug(f'{current_state} - (start) -> S0')
    watch.start(0)
    LED.switch_on({LEDEnum.green})  # turn on LED green
    return 'S0'


def do_move0() -> str:

    p, t0, c0, t1, c1 = watch.get_status()
    # next player
    logging.debug(f'{current_state} - (move) -> S1')
    watch.start(1)
    LED.switch_on({LEDEnum.red})  # turn on LED red

    # get picture
    # analyze
    # calc move
    # store move
    picture = vt.read()
    # cv2.imshow("Live", picture)  # todo: remove display

    # todo: move in Queue
    return 'S1'


def do_pause0() -> str:
    logging.debug(f'{current_state} - (pause) -> P0')
    watch.pause()
    LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green, yellow
    return 'P0'


def do_resume0() -> str:
    logging.debug(f'{current_state} - (resume) -> S0')
    watch.resume()
    LED.switch_on({LEDEnum.green})  # turn on LED green
    return 'S0'


def do_valid_challenge0() -> str:
    logging.debug(f'{current_state} - (valid challenge) -> P0')
    watch.display.add_remove_tiles(1)
    # todo: valid challenge in Queue
    LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green, yellow
    return 'P0'


def do_invalid_challenge0() -> str:
    logging.debug(f'{current_state} - (invalid challenge) -> P0 (-{config.MALUS_DOUBT:2d})')  # -10
    watch.display.add_malus(0)  # player 1
    LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green
    # todo: invalid challenge in Queue
    return 'P0'


def do_start1() -> str:
    logging.debug(f'{current_state} - (start) -> S1')
    watch.start(1)
    LED.switch_on({LEDEnum.red})  # turn on LED red
    return 'S1'


def do_move1() -> str:
    p, t1, c1, t2, c2 = watch.get_status()
    # next state
    logging.debug(f'{current_state} - (move) -> S0')
    watch.start(0)
    LED.switch_on({LEDEnum.green})  # turn on LED green

    # get picture
    # analyze
    # calc move
    # store move
    picture = vt.read()
    # cv2.imshow("Live", picture)  # todo: remove display

    # todo: move in Queue
    return 'S0'


def do_resume1() -> str:
    logging.debug(f'{current_state} - (resume) -> S1')
    watch.resume()
    LED.switch_on({LEDEnum.red})  # turn on LED red
    return 'S1'


def do_pause1() -> str:
    logging.debug(f'{current_state} - (pause) -> P1')
    watch.pause()
    LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
    return 'P1'


def do_valid_challenge1() -> str:
    logging.debug(f'{current_state} - (valid challenge) -> P1')
    watch.display.add_remove_tiles(0)
    # todo: valid challenge in Queue
    LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
    return 'P1'


def do_invalid_challenge1() -> str:
    logging.debug(f'{current_state} - (invalid challenge) -> P1 (-{config.MALUS_DOUBT:2d})')  # -10
    watch.display.add_malus(1)  # player 2
    # todo: invalid challenge in Queue
    LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
    return 'P1'


def do_reset() -> str:
    global current_state
    logging.debug(f'{current_state} - (reset) -> START')
    LED.switch_on({})  # type: ignore
    watch.reset()
    # todo: check for upload
    # todo: reset app data
    current_state = 'START'
    do_ready()
    return current_state


def do_reboot() -> str:
    import signal
    global current_state

    logging.debug(f'{current_state} - (reboot) -> START')
    watch.display.show_boot()  # Display message REBOOT
    # todo: check for upload
    LED.switch_on({})  # type: ignore
    watch.timer.stop()
    watch.display.stop()
    current_state = 'START'
    # todo: camera aus?
    print('jetzt pause beenden')
    signal.alarm(1)
    return 'START'


def do_config() -> str:
    global current_state
    logging.debug(f'{current_state} - (config) -> START')
    watch.reset()
    watch.display.show_config()  # Display message CONFIG
    # todo: check for upload
    LED.switch_on({})  # type: ignore
    current_state = 'START'
    return current_state


def press_button(button: str) -> None:
    global current_state
    # logging.debug(f'button press: {button}')
    try:
        current_state = state[(current_state, button.lower())]()
    except KeyError:
        logging.debug('Key Error - ignore')


def release_button(button: str) -> None:
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
