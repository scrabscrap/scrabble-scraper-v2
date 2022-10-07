import base64
import logging
import logging.config
import os
import subprocess
import urllib.parse
from time import sleep

import cv2
import util
from api_server_thread import ApiServer
from config import config
from flask import redirect, render_template, url_for
from gpiozero import Device
from gpiozero.pins.mock import MockFactory
from hardware.led import LEDEnum
from scrabblewatch import ScrabbleWatch
from state import State
from threadpool import pool
from timer_thread import RepeatedTimer

Device.pin_factory = MockFactory()

TEMPLATE_FOLDER = f'{os.path.dirname(__file__) or "."}/../src/templates'
STATIC_FOLDER = f'{os.path.dirname(__file__) or "."}/../src/static'


def doubt0():
    State().press_button('DOUBT0')
    return redirect(url_for('simulator'))


def doubt1():
    State().press_button('DOUBT1')
    return redirect(url_for('simulator'))


def green():
    State().press_button('GREEN')
    sleep(0.7)
    return redirect(url_for('simulator'))


def red():
    State().press_button('RED')
    sleep(0.7)
    return redirect(url_for('simulator'))


def yellow():
    State().press_button('YELLOW')
    return redirect(url_for('simulator'))


def reset():
    State().press_button('RESET')
    ApiServer.cam.stream.cnt = 0  # type: ignore
    return redirect(url_for('simulator'))


def cam_first():
    logging.debug('first')
    ApiServer.cam.stream.cnt = 0  # type: ignore
    return redirect(url_for('simulator'))


def cam_prev():
    logging.debug('prev')
    if ApiServer.cam.stream.cnt > 0:  # type: ignore
        ApiServer.cam.stream.cnt -= 1  # type: ignore
    return redirect(url_for('simulator'))


def cam_next():
    logging.debug('next')
    ApiServer.cam.stream.cnt += 1 if os.path.isfile(  # type: ignore
        ApiServer.cam.stream.formatter.format(ApiServer.cam.stream.cnt + 1)) else 0  # type: ignore
    return redirect(url_for('simulator'))


def cam_last():
    logging.debug('last')
    while os.path.isfile(ApiServer.cam.stream.formatter.format(ApiServer.cam.stream.cnt + 1)):  # type: ignore
        ApiServer.cam.stream.cnt += 1  # type: ignore
    return redirect(url_for('simulator'))


def simulator() -> str:
    logging.debug(f'thread queue len {len(pool._threads)}')
    # display time
    _, t0, _, t1, _ = State().watch.get_status()
    m1, s1 = divmod(abs(1800 - t0), 60)
    m2, s2 = divmod(abs(1800 - t1), 60)
    left = f'-{m1:1d}:{s1:02d}' if 1800 - \
        t0 < 0 else f'{m1:02d}:{s1:02d}'
    right = f'-{m2:1d}:{s2:02d}' if 1800 - \
        t1 < 0 else f'{m2:02d}:{s2:02d}'
    # get current picture
    png_current = None
    game = State().game
    if (len(game.moves) > 0) and (game.moves[-1].img is not None):
        pic = game.moves[-1].img
        _, pic_buf_arr = cv2.imencode(".jpg", pic)
        png_current = urllib.parse.quote(base64.b64encode(pic_buf_arr))

    # get next picture
    img = ApiServer.cam.read(peek=True)  # type: ignore
    _, im_buf_arr = cv2.imencode(".jpg", img)
    png_next = urllib.parse.quote(base64.b64encode(im_buf_arr))
    #show log
    if os.path.exists(f'{config.LOG_DIR}/messages.log'):
        p1 = subprocess.run(['tail', '-75', f'{config.LOG_DIR}/messages.log'], check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log_out = p1.stdout.decode()
    else:
        log_out = '## empty ##'

    return render_template('simulator.html', version=ApiServer.scrabscrap_version,
                           img_next=png_next, img_current=png_current,log=log_out,
                           green=LEDEnum.green.value, yellow=LEDEnum.yellow.value, red=LEDEnum.red.value,
                           left=left, right=right)


def main():
    from threading import Event

    from hardware.camera_thread import Camera, CameraEnum

    logging.config.fileConfig(fname=config.WORK_DIR + '/log.conf',
                              disable_existing_loggers=False,
                              defaults={'level': 'DEBUG',
                                        'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})

    # flask log only error
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # set Mock-Camera
    cam = Camera(useCamera=CameraEnum.FILE)
    cam_event = Event()
    _ = pool.submit(cam.update, cam_event)

    # set Watch
    watch = ScrabbleWatch()
    timer = RepeatedTimer(1, watch.tick)
    timer_event = Event()
    _ = pool.submit(timer.tick, timer_event)

    api = ApiServer()
    ApiServer.cam = cam  # type: ignore

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
    api.app.add_url_rule('/simulator', 'simulator', simulator)

    # start State-Machine
    state = State(cam=cam, watch=watch)
    state.do_ready()

    api.start_server(host=util.get_ipv4())

    api.stop_server()
    cam_event.set()
    timer_event.set()


if __name__ == '__main__':
    main()
