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

from scrabblewatch import ScrabbleWatch  # pylint: disable=wrong-import-order

# display fast boot message on display
ScrabbleWatch.display.show_boot()  # Boot Message

# ruff: noqa: E402
import atexit
import logging
import logging.config
import signal
import sys
from signal import pause
from threading import Event

from api_server_thread import ApiServer
from config import config, version
from hardware import camera
from state import State
from threadpool import pool
from timer_thread import RepeatedTimer

logging.config.fileConfig(
    fname=f'{config.path.work_dir}/log.conf',
    disable_existing_loggers=True,
    defaults={'level': 'DEBUG', 'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'},
)


def main() -> None:
    """entry point for scrabscrap"""

    def log_exception_handler(exctype, value, tb):
        import traceback

        logging.exception(''.join(traceback.format_exception(exctype, value, tb)))
        sys.__excepthook__(exctype, value, tb)  # calls default excepthook

    def _cleanup():
        atexit.unregister(_cleanup)
        logging.debug('main-_atexit')
        api.stop_server()
        timer.cancel()
        camera.cam.cancel()
        pool.shutdown(cancel_futures=True)

    def signal_alarm(signum, _) -> None:
        import os

        logging.debug(f'Alarm handler called with signal {signum}')
        signal.alarm(0)
        _cleanup()
        if config.system.quit in ('reboot'):
            os.system('sudo shutdown -r now')
        elif config.system.quit in ('shutdown'):
            os.system('sudo shutdown now')
        elif config.system.quit in ('restart'):
            sys.exit(4)
        sys.exit(0)

    sys.excepthook = log_exception_handler
    logging.info('####################################################################')
    logging.info('## ScrabScrap loading ...                                         ##')
    logging.info('####################################################################')

    logging.info(f'Version: {version.git_version}')
    logging.info(f'Git branch: {version.git_branch}')
    logging.info(f'Git commit: {version.git_commit}')

    signal.signal(signal.SIGALRM, signal_alarm)
    atexit.register(_cleanup)

    # start camera
    _ = pool.submit(camera.cam.update, Event())
    camera.cam.log_camera_info()

    # create Timer
    ScrabbleWatch.display.show_boot()  # Boot Message
    timer = RepeatedTimer(1, ScrabbleWatch.tick)
    timer.start()

    # start api server
    api = ApiServer()
    _ = pool.submit(api.start_server)

    # init State Machine
    State.init()

    logging.info('####################################################################')
    logging.info('## ScrabScrap ready                                               ##')
    logging.info('####################################################################')

    # Run until Exit with alarm(1)
    pause()


if __name__ == '__main__':
    main()
