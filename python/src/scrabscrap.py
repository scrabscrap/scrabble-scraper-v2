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
import atexit
import logging
import logging.config
import signal
import sys
from signal import pause
from threading import Event
from time import sleep

from config import config

logging.config.fileConfig(fname=f'{config.work_dir}/log.conf',
                          disable_existing_loggers=False,
                          defaults={'level': 'DEBUG',
                                    'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})


from api_server_thread import ApiServer
from hardware.camera_thread import Camera
from scrabblewatch import ScrabbleWatch
from state import State
from threadpool import pool
from timer_thread import RepeatedTimer

cleanup_done = False  # pylint: disable=C0103 # not a contant see _cleanup()


def main() -> None:
    """entry point for scrabscrap"""

    def _cleanup():
        global cleanup_done  # pylint: disable=W0603,C0103 # not a contant see _cleanup()

        logging.debug(f'main-_atexit {cleanup_done}')
        if not cleanup_done:
            cleanup_done = True
            api_future.cancel()
            cam_future.cancel()
            timer_future.cancel()
            api.stop_server()
            cam_event.set()
            timer_event.set()
            pool.shutdown()

    def signal_alarm(signum, _) -> None:
        import os

        logging.debug(f'Alarm handler called with signal {signum}')
        _cleanup()
        signal.alarm(0)
        if config.system_quit in ('reboot'):
            os.system('sudo shutdown -r now')
            sys.exit(0)
        elif config.system_quit in ('shutdown'):
            os.system('sudo shutdown now')
            sys.exit(0)

    # def signal_handler(signum, _) -> None:
    #     logging.debug(f'Signal handler called with signal {signum}')
    #     _cleanup()

    signal.signal(signal.SIGALRM, signal_alarm)
    # signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(_cleanup)
    # create Timer
    watch = ScrabbleWatch()
    watch.display.show_boot()  # Boot Message
    timer = RepeatedTimer(1, watch.tick)
    timer_event = Event()
    timer_future = pool.submit(timer.tick, timer_event)

    cam = None
    sleep(2)  # wait for camera
    try:
        # open Camera
        cam = Camera()
        # cam = MockCamera()
        cam_event = Event()
        cam_future = pool.submit(cam.update, cam_event)
    except Exception as oops:  # type: ignore # pylint: disable=W0703
        logging.error(f'can not open camera {oops}')

    # start api server
    api = ApiServer(cam=cam)
    api_future = pool.submit(api.start_server)

    # start State-Machine
    state = State(cam=cam, watch=watch)
    # set callback for Button Events
    state.init()

    if cam is None:
        watch.display.show_cam_err()
    # Run until Exit with alarm(1)
    pause()


if __name__ == '__main__':
    main()
