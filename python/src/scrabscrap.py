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

from config import Config

logging.config.fileConfig(fname=f'{Config.work_dir()}/log.conf',
                          disable_existing_loggers=False,
                          defaults={'level': 'DEBUG',
                                    'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})


import hardware.camera_thread as cam
from api_server_thread import ApiServer
from scrabblewatch import ScrabbleWatch
from state import State
from threadpool import pool
from timer_thread import RepeatedTimer

cleanup_done = False  # pylint: disable=invalid-name


def main() -> None:
    """entry point for scrabscrap"""

    def _cleanup():
        global cleanup_done  # pylint: disable=invalid-name,global-statement
        # not a constant see _cleanup()

        logging.debug(f'main-_atexit {cleanup_done}')
        if not cleanup_done:
            cleanup_done = True
            api.stop_server()
            timer.cancel()
            cam.cancel()
            pool.shutdown(cancel_futures=True)

    def signal_alarm(signum, _) -> None:
        import os

        logging.debug(f'Alarm handler called with signal {signum}')
        _cleanup()
        signal.alarm(0)
        if Config.system_quit() in ('reboot'):
            os.system('sudo shutdown -r now')
            sys.exit(0)
        elif Config.system_quit() in ('shutdown'):
            os.system('sudo shutdown now')
            sys.exit(0)

    logging.info('####################################################################')
    logging.info('## ScrabScrap loading ...                                         ##')
    logging.info('####################################################################')

    signal.signal(signal.SIGALRM, signal_alarm)
    atexit.register(_cleanup)

    # create Timer
    ScrabbleWatch.display.show_boot()  # Boot Message
    timer = RepeatedTimer(1, ScrabbleWatch.tick)
    _ = pool.submit(timer.tick, Event())

    cam.init()
    try:
        _ = pool.submit(cam.update, Event())
    except Exception as oops:  # type: ignore # pylint: disable=broad-exception-caught
        logging.exception(f'can not open camera {oops}')

    # start api server
    api = ApiServer()
    _ = pool.submit(api.start_server)

    # init State Machine
    State.init()

    if cam is None:
        ScrabbleWatch.display.show_cam_err()

    logging.info('####################################################################')
    logging.info('## ScrabScrap ready                                               ##')
    logging.info('####################################################################')

    # Run until Exit with alarm(1)
    pause()


if __name__ == '__main__':
    main()
