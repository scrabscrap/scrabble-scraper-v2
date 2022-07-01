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
import signal
from signal import pause
from threading import Event

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')

from button import Button
from state import State
from camera import Camera
from simulate.mockcamera import MockCamera
from threadpool import pool
from scrabblewatch import ScrabbleWatch
from repeatedtimer import RepeatedTimer


def main() -> None:

    # create Timer
    watch = ScrabbleWatch()
    watch.display.show_boot()  # Boot Message
    timer = RepeatedTimer(1, watch.tick)
    timer_event = Event()
    timer_future = pool.submit(timer.tick, timer_event)

    # open Camera
    # cam = Camera()
    cam = MockCamera()
    cam_event = Event()
    cam_future = pool.submit(cam.update, cam_event)

    # start Button-Handler
    button_handler = Button()
    # start State-Machine
    state = State(watch)

    # set callback for Button Events
    button_handler.start(state)

    # set Display to Ready
    state.do_ready()

    # Run until Exit with alarm(1)
    pause()

    # cleanup pool
    cam_event.set()
    timer_event.set()

    # reset alarm
    signal.alarm(0)
    
    # cleanup with atexit Methods
    exit(0)


if __name__ == '__main__':
    main()
