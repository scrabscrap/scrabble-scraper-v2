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
import os
import subprocess
import urllib.parse
from time import sleep

import cv2
from flask import redirect, render_template, request, url_for
from gpiozero import Device
from gpiozero.pins.mock import MockFactory

from api_server_thread import ApiServer
from config import config
from hardware import camera
from hardware.led import LEDEnum
from scrabblewatch import ScrabbleWatch
from state import State
from threadpool import pool
from timer_thread import RepeatedTimer

Device.pin_factory = MockFactory()

# TEMPLATE_FOLDER = os.path.abspath(f'{os.path.dirname(__file__) or "."}/../src/templates')
# STATIC_FOLDER = os.path.abspath(f'{os.path.dirname(__file__) or "."}/../src/static')


def doubt0():
    """simulate doubt player 0"""
    State.press_button('DOUBT0')
    return redirect(url_for('simulator'))


def doubt1():
    """simulate doubt player 1"""
    State.press_button('DOUBT1')
    return redirect(url_for('simulator'))


def green():
    """simulate press green button"""
    State.press_button('GREEN')
    if State.last_submit is not None:
        while not State.last_submit.done():  # type: ignore
            sleep(0.01)
    return redirect(url_for('simulator'))


def red():
    """simulate press red button"""
    State.press_button('RED')
    if State.last_submit is not None:
        while not State.last_submit.done():  # type: ignore
            sleep(0.01)
    return redirect(url_for('simulator'))


def yellow():
    """simulate press yellow button"""
    State.press_button('YELLOW')
    return redirect(url_for('simulator'))


def reset():
    """simulate press reset"""
    State.press_button('RESET')
    camera.cam.conter = 1  # type: ignore
    return redirect(url_for('simulator'))


def cam_first():
    """skip to first image"""
    camera.cam.counter = 1  # type: ignore
    return redirect(url_for('simulator'))


def cam_prev():
    """skip to previous image"""
    logging.debug('prev')
    if camera.cam.counter > 1:  # type: ignore
        camera.cam.counter -= 1  # type: ignore
    return redirect(url_for('simulator'))


def cam_next():
    """skip to next image"""
    logging.debug('next')
    camera.cam.counter += 1 if os.path.isfile(  # type: ignore
        camera.cam.formatter.format(camera.cam.counter + 1)) else 0  # type: ignore
    return redirect(url_for('simulator'))


def cam_last():
    """skip to last image"""
    logging.debug('last')
    while os.path.isfile(camera.cam.formatter.format(camera.cam.counter + 1)):  # type: ignore
        camera.cam.counter += 1  # type: ignore
    return redirect(url_for('simulator'))


def open_folder():
    """select folder for images"""
    folder = request.args.get('folder')
    logging.debug(f'try to open {folder}')
    ini_file = os.path.abspath(f'{config.src_dir}/../test/{folder}/scrabble.ini')
    if os.path.exists(ini_file):
        config.reload(ini_file=ini_file)
        camera.cam.counter = 1  # type: ignore
        camera.cam.formatter = config.simulate_path  # type: ignore
    else:
        logging.warning(f'INI File not found / invalid: {ini_file}')
    return redirect(url_for('simulator'))


def simulator() -> str:
    """"render simulator on web page"""
    # get simulate folders
    list_of_dir = [f for f in os.listdir(f'{config.src_dir}/../test')
                   if os.path.isdir(f'{config.src_dir}/../test/{f}') and f.startswith('game')]
    # display time
    _, (time0, time1), _ = ScrabbleWatch.status()
    minutes, seconds = divmod(abs(1800 - time0), 60)
    left = f'-{minutes:1d}:{seconds:02d}' if 1800 - time0 < 0 else f'{minutes:02d}:{seconds:02d}'
    minutes, seconds = divmod(abs(1800 - time1), 60)
    right = f'-{minutes:1d}:{seconds:02d}' if 1800 - time1 < 0 else f'{minutes:02d}:{seconds:02d}'
    # get current picture
    png_current = None
    board = ''
    game = State.game
    if (len(game.moves) > 0) and (game.moves[-1].img is not None):
        _, pic_buf_arr = cv2.imencode(".jpg", game.moves[-1].img)
        png_current = urllib.parse.quote(base64.b64encode(pic_buf_arr))
        board = f'Score: {game.moves[-1].score} / {game.moves[-1].points}\n{game.board_str()}'
    # get next picture
    img = camera.cam.read(peek=True)  # type: ignore
    _, pic_buf_arr = cv2.imencode(".jpg", img)
    png_next = urllib.parse.quote(base64.b64encode(pic_buf_arr))
    # show log
    if os.path.exists(f'{config.log_dir}/messages.log'):
        process = subprocess.run(['tail', '-75', f'{config.log_dir}/messages.log'], check=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log_out = process.stdout.decode()
    else:
        log_out = '## empty ##'

    return render_template('simulator.html', apiserver=ApiServer,
                           img_next=png_next, img_current=png_current, log=log_out,
                           green=LEDEnum.green.value, yellow=LEDEnum.yellow.value, red=LEDEnum.red.value,
                           left=left, right=right, folder=list_of_dir, board=board)


def main():
    """used to start the simulator"""

    from threading import Event

    from display import DisplayMock

    logging.config.fileConfig(fname=config.work_dir + '/log.conf',
                              disable_existing_loggers=False,
                              defaults={'level': 'DEBUG',
                                        'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})

    # flask log only error
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # set Mock-Camera
    camera.switch_camera('file')
    _ = pool.submit(camera.cam.update, Event())
    camera.cam.resize = False

    # set Watch
    ScrabbleWatch.display = DisplayMock()
    timer = RepeatedTimer(1, ScrabbleWatch.tick)
    _ = pool.submit(timer.tick, Event())

    api = ApiServer()

    api.app.add_url_rule('/simulator/red', 'red', red)
    api.app.add_url_rule('/simulator/green', 'green', green)
    api.app.add_url_rule('/simulator/yellow', 'yellow', yellow)
    api.app.add_url_rule('/simulator/doubt0', 'doubt0', doubt0)
    api.app.add_url_rule('/simulator/doubt1', 'doubt1', doubt1)
    api.app.add_url_rule('/simulator/reset', 'reset', reset)
    api.app.add_url_rule('/simulator/first', 'first', cam_first)
    api.app.add_url_rule('/simulator/prev', 'prev', cam_prev)
    api.app.add_url_rule('/simulator/next', 'next', cam_next)
    api.app.add_url_rule('/simulator/last', 'last', cam_last)
    api.app.add_url_rule('/simulator/open', 'open', open_folder)
    api.app.add_url_rule('/simulator', 'simulator', simulator)

    # start State-Machine
    State.do_ready()
    logging.debug(f'#### workdir {config.work_dir}')
    api.start_server(port=5050, simulator=True)

    api.stop_server()
    camera.cam.cancel()
    timer.cancel()


if __name__ == '__main__':
    main()
