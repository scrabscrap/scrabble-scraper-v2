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

import base64
import logging
import logging.config
import urllib.parse
from pathlib import Path

import cv2
from flask import redirect, render_template, request, url_for
from gpiozero import Device
from gpiozero.pins.mock import MockFactory

from config import config, version
from hardware import camera
from hardware.led import LEDEnum
from scrabblewatch import ScrabbleWatch
from state import State
from utils.threadpool import command_queue, pool
from utils.timer_thread import RepeatedTimer

from admin.server import app, start_server, stop_server
from admin.server_context import ctx

Device.pin_factory = MockFactory()
current_counter: int = 0
list_of_dir: list[str] = []
logger = logging.getLogger()

# TEMPLATE_FOLDER = os.path.abspath(f'{os.path.dirname(__file__) or "."}/../src/templates')
# STATIC_FOLDER = os.path.abspath(f'{os.path.dirname(__file__) or "."}/../src/static')


def doubt0():
    """simulate doubt player 0"""
    State.press_button('DOUBT0')
    command_queue.join()
    return redirect(url_for('simulator'))


def doubt1():
    """simulate doubt player 1"""
    State.press_button('DOUBT1')
    command_queue.join()
    return redirect(url_for('simulator'))


def green():
    """simulate press green button"""
    global current_counter  # pylint: disable=global-statement

    current_counter = camera.cam.counter  # type: ignore
    State.press_button('GREEN')
    command_queue.join()
    return redirect(url_for('simulator'))


def red():
    """simulate press red button"""
    global current_counter  # pylint: disable=global-statement

    current_counter = camera.cam.counter  # type: ignore
    State.press_button('RED')
    command_queue.join()
    return redirect(url_for('simulator'))


def yellow():
    """simulate press yellow button"""
    State.press_button('YELLOW')
    command_queue.join()
    return redirect(url_for('simulator'))


def reset():
    """simulate press reset"""
    State.press_button('RESET')
    command_queue.join()
    camera.cam.counter = 1  # type: ignore
    return redirect(url_for('simulator'))


def cam_first():
    """skip to first image"""
    camera.cam.counter = 1  # type: ignore
    return redirect(url_for('simulator'))


def cam_prev():
    """skip to previous image"""
    logger.debug('prev')
    if camera.cam.counter > 1:  # type: ignore
        camera.cam.counter -= 1  # type: ignore
    return redirect(url_for('simulator'))


def cam_next():
    """skip to next image"""
    logger.debug('next')
    camera.cam.counter += 1 if Path(camera.cam.formatter.format(camera.cam.counter + 1)).is_file() else 0  # type: ignore
    return redirect(url_for('simulator'))


def cam_last():
    """skip to last image"""
    logger.debug('last')
    while Path(camera.cam.formatter.format(camera.cam.counter + 1)).is_file():  # type: ignore
        camera.cam.counter += 1  # type: ignore
    return redirect(url_for('simulator'))


def open_folder():
    """select folder for images"""
    folder = request.args.get('folder')
    logger.debug(f'try to open {folder}')
    if folder is not None:
        ini_file = (config.path.src_dir.parent / 'test' / folder / 'scrabble.ini').resolve()
        if ini_file.exists():
            config.reload(ini_file=str(ini_file))
            camera.cam.counter = 1  # type: ignore
            camera.cam.formatter = config.development.simulate_path  # type: ignore
        else:
            logger.warning(f'INI File not found / invalid: {ini_file}')
    return redirect(url_for('simulator'))


def simulator() -> str:
    """ "render simulator on web page"""
    # display time
    _, (time0, time1), _ = ScrabbleWatch.status()
    minutes, seconds = divmod(abs(1800 - time0), 60)
    left = f'-{minutes:1d}:{seconds:02d}' if 1800 - time0 < 0 else f'{minutes:02d}:{seconds:02d}'
    minutes, seconds = divmod(abs(1800 - time1), 60)
    right = f'-{minutes:1d}:{seconds:02d}' if 1800 - time1 < 0 else f'{minutes:02d}:{seconds:02d}'
    # get current picture
    png_current = None
    game = State.ctx.game
    if (len(game.moves) > 0) and (game.moves[-1].img is not None):
        _, pic_buf_arr = cv2.imencode('.jpg', game.moves[-1].img)
        png_current = urllib.parse.quote(base64.b64encode(bytes(pic_buf_arr)))
        current_file = camera.cam.formatter.format(current_counter).split('/')  # type: ignore # using CameraFile
        current_file_str = '/'.join([current_file[-2], current_file[-1]]) if current_file else ''  # type: ignore
    else:
        current_file_str = ''
        png_current = None
    # get next picture
    img = camera.cam.read(peek=True)  # type: ignore
    _, pic_buf_arr = cv2.imencode('.jpg', img)
    png_next = urllib.parse.quote(base64.b64encode(bytes(pic_buf_arr)))
    next_file = ''
    if isinstance(camera.cam, camera.CameraFile):
        next_file = camera.cam._formatter.format(camera.cam._counter).split('/')[-1]

    return render_template(
        'simulator.html',
        apiserver=ctx,
        img_next=png_next,
        img_current=png_current,
        green=LEDEnum.green.value,  # pylint: disable=duplicate-code
        yellow=LEDEnum.yellow.value,
        red=LEDEnum.red.value,
        left=left,
        right=right,
        folder=list_of_dir,
        next_file=next_file,
        current_file=current_file_str,
    )


# pylint: disable=duplicate-code
def main():
    """used to start the simulator"""
    global list_of_dir  # pylint: disable=global-statement

    import sys
    from threading import Event

    from display import Display

    def log_exception_handler(exctype, value, tb):
        import traceback

        logger.exception(''.join(traceback.format_exception(exctype, value, tb)))
        sys.__excepthook__(exctype, value, tb)  # calls default excepthook

    logging.config.fileConfig(
        fname=str(config.path.work_dir / 'log.conf'),
        disable_existing_loggers=False,
        defaults={'level': 'DEBUG', 'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'},
    )

    # flask log only error
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    sys.excepthook = log_exception_handler
    logger.info('####################################################################')
    logger.info('## Simulator loading ...                                          ##')
    logger.info('####################################################################')

    logger.info(f'Version: {version.git_version}')
    logger.info(f'Git branch: {version.git_branch}')
    logger.info(f'Git commit: {version.git_commit}')

    # get simulate folders
    test_dir = Path(config.path.src_dir).resolve().parent / 'test'
    list_of_dir = sorted([f.name for f in test_dir.iterdir() if f.is_dir() and f.name.startswith('game')])
    # set Mock-Camera
    camera.switch_camera('file')
    _ = pool.submit(camera.cam.update, Event())
    if isinstance(camera.cam, camera.CameraFile):
        camera.cam.resize = False

    # set Watch
    ScrabbleWatch.display = Display()
    timer = RepeatedTimer(1, ScrabbleWatch.tick)
    timer.start()

    app.add_url_rule('/simulator/red', 'red', red)
    app.add_url_rule('/simulator/green', 'green', green)
    app.add_url_rule('/simulator/yellow', 'yellow', yellow)
    app.add_url_rule('/simulator/doubt0', 'doubt0', doubt0)
    app.add_url_rule('/simulator/doubt1', 'doubt1', doubt1)
    app.add_url_rule('/simulator/reset', 'reset', reset)
    app.add_url_rule('/simulator/first', 'first', cam_first)
    app.add_url_rule('/simulator/prev', 'prev', cam_prev)
    app.add_url_rule('/simulator/next', 'next', cam_next)
    app.add_url_rule('/simulator/last', 'last', cam_last)
    app.add_url_rule('/simulator/open', 'open', open_folder)
    app.add_url_rule('/simulator', 'simulator', simulator)

    # start State-Machine
    State.do_new_game()
    logger.debug(f'#### workdir {config.path.work_dir}')
    logger.info('####################################################################')

    start_server(port=5050, simulator=True)

    stop_server()
    camera.cam.cancel()
    timer.cancel()


if __name__ == '__main__':
    main()
