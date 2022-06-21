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


def do_ready() -> None:
    global current_state
    watch.display.show_ready()
    current_state = 'START'


def do_start1() -> None:
    global current_state
    logging.debug(f'{current_state} -> S1')
    watch.start(0)
    LED.switch_on({LEDEnum.green})  # turn on LED green
    current_state = 'S1'


def do_move1() -> None:
    global current_state

    p, t1, c1, t2, c2 = watch.get_status()
    # next player
    logging.debug(f'{current_state} -> S2')
    watch.start(1)
    LED.switch_on({LEDEnum.red})  # turn on LED red

    # get picture
    # analyze
    # calc move
    # store move
    picture = vt.read()
    # cv2.imshow("Live", picture)  # todo: remove display

    # todo: move in Queue
    current_state = 'S2'


def do_pause1() -> None:
    global current_state
    logging.debug(f'{current_state} -> P1')
    watch.pause()
    LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green, yellow
    current_state = 'P1'


def do_resume1() -> None:
    global current_state
    logging.debug(f'{current_state} -> S1')
    watch.resume()
    LED.switch_on({LEDEnum.green})  # turn on LED green
    current_state = 'S1'


def do_valid_challenge1() -> None:
    global current_state
    logging.debug(f'{current_state} -> P1')
    watch.display.add_remove_tiles(1)
    # todo: valid challenge in Queue
    LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green, yellow
    current_state = 'P1'


def do_invalid_challenge1() -> None:
    global current_state
    logging.debug(f'{current_state} -> P1 (-{config.MALUS_DOUBT:2d})')  # -10
    watch.display.add_malus(0)  # player 1
    # todo: invalid challenge in Queue
    LED.switch_on({LEDEnum.green, LEDEnum.yellow})  # turn on LED green
    current_state = 'P1'


def do_start2() -> None:
    global current_state
    logging.debug(f'{current_state} -> S2')
    watch.start(1)
    LED.switch_on({LEDEnum.red})  # turn on LED red
    current_state = 'S2'


def do_move2() -> None:
    global current_state
    p, t1, c1, t2, c2 = watch.get_status()
    # next state
    logging.debug(f'{current_state} -> S1')
    watch.start(0)
    LED.switch_on({LEDEnum.green})  # turn on LED green

    # get picture
    # analyze
    # calc move
    # store move
    picture = vt.read()
    # cv2.imshow("Live", picture)  # todo: remove display

    # todo: move in Queue
    current_state = 'S1'


def do_resume2() -> None:
    global current_state
    logging.debug(f'{current_state} -> S2')
    watch.resume()
    LED.switch_on({LEDEnum.red})  # turn on LED red
    current_state = 'S2'


def do_pause2() -> None:
    global current_state
    logging.debug(f'{current_state} -> P2')
    watch.pause()
    LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
    current_state = 'P2'


def do_valid_challenge2() -> None:
    global current_state
    logging.debug(f'{current_state} -> P2')
    watch.display.add_remove_tiles(0)
    # todo: valid challenge in Queue
    LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
    current_state = 'P2'


def do_invalid_challenge2() -> None:
    global current_state
    logging.debug(f'{current_state} -> P2 (-{config.MALUS_DOUBT:2d})')  # -10
    watch.display.add_malus(1)  # player 2
    # todo: invalid challenge in Queue
    LED.switch_on({LEDEnum.red, LEDEnum.yellow})  # turn on LED red, yellow
    current_state = 'P2'


def do_reset() -> None:
    global current_state
    logging.debug(f'{current_state} - (reset) -> START')
    watch.reset()
    watch.display.show_reset()  # Display message RESET
    # todo: check for upload
    # todo: reset app data
    LED.switch_on({})  # type: ignore
    do_ready()


def do_reboot() -> None:
    import signal

    global current_state
    logging.debug(f'{current_state} - (reboot) -> START')
    watch.display.show_boot()  # Display message REBOOT
    # todo: check for upload
    LED.switch_on({})  # type: ignore
    watch.timer.stop()
    watch.display.stop()
    # todo: camera aus?
    print('jetzt pause beenden')
    signal.alarm(1)


def do_config() -> None:
    global current_state
    logging.debug(f'{current_state} - (config) -> START')
    watch.reset()
    watch.display.show_config()  # Display message CONFIG
    # todo: check for upload
    LED.switch_on({})  # type: ignore
    current_state = 'START'


def press_button(button: str) -> None:
    logging.debug(f'button press: {button}')
    try:
        state[(current_state, button.lower())]()
    except KeyError:
        logging.debug('Key Error - ignore')


def release_button(button: str) -> None:
    logging.debug(f'button release: {button}')


# START, pause => not supported
state: dict[tuple[str, str], Callable] = {
    ('START', 'green'): do_start2,
    ('START', 'red'): do_start1,
    ('START', 'reset'): do_reset,
    ('START', 'reboot'): do_reboot,
    ('START', 'config'): do_config,
    ('S1', 'green'): do_move1,
    ('S1', 'yellow'): do_pause1,
    ('P1', 'red'): do_resume1,
    ('P1', 'yellow'): do_resume1,
    ('P1', 'doubt1'): do_valid_challenge1,
    ('P1', 'doubt2'): do_invalid_challenge1,
    ('P1', 'reset'): do_reset,
    ('P1', 'reboot'): do_reboot,
    ('P1', 'config'): do_config,
    ('S2', 'red'): do_move2,
    ('S2', 'yellow'): do_pause2,
    ('P2', 'green'): do_resume2,
    ('P2', 'yellow'): do_resume2,
    ('P2', 'doubt2'): do_valid_challenge2,
    ('P2', 'doubt1'): do_invalid_challenge2,
    ('P2', 'reset'): do_reset,
    ('P2', 'reboot'): do_reboot,
    ('P2', 'config'): do_config,
}
