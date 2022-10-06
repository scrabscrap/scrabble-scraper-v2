import base64
import logging
import logging.config
import os
import subprocess
import urllib.parse
from time import sleep

import cv2
from api_server_thread import ApiServer
from config import config
from flask import redirect, render_template, url_for
from gpiozero import Device
from gpiozero.pins.mock import MockFactory
from hardware.button import ButtonEnum
from state import State
from threadpool import pool

TEMPLATE_FOLDER = f'{os.path.dirname(__file__) or "."}/../src/templates'
STATIC_FOLDER = f'{os.path.dirname(__file__) or "."}/../src/static'

Device.pin_factory = MockFactory()
PIN_GREEN = Device.pin_factory.pin(ButtonEnum.GREEN.value)
PIN_DOUBT0 = Device.pin_factory.pin(ButtonEnum.DOUBT0.value)
PIN_YELLOW = Device.pin_factory.pin(ButtonEnum.YELLOW.value)
PIN_RED = Device.pin_factory.pin(ButtonEnum.RED.value)
PIN_DOUBT1 = Device.pin_factory.pin(ButtonEnum.DOUBT1.value)
PIN_RESET = Device.pin_factory.pin(ButtonEnum.RESET.value)
PIN_REBOOT = Device.pin_factory.pin(ButtonEnum.REBOOT.value)
PIN_CONFIG = Device.pin_factory.pin(ButtonEnum.CONFIG.value)


def _press_button(pin, wait=0.001):
    logging.debug(f'press {str(pin)}')
    pin.drive_high()
    sleep(wait)
    pin.drive_low()


def doubt0():
    _press_button(PIN_DOUBT0)
    return redirect(url_for('simulator'))


def doubt1():
    _press_button(PIN_DOUBT1)
    return redirect(url_for('simulator'))


def green():
    _press_button(PIN_GREEN)
    return redirect(url_for('simulator'))


def red():
    _press_button(PIN_RED)
    return redirect(url_for('simulator'))


def yellow():
    _press_button(PIN_YELLOW)
    return redirect(url_for('simulator'))


def reset():
    _press_button(PIN_RESET)
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
    img = ApiServer.cam.read(peek=True)  # type: ignore
    _, im_buf_arr = cv2.imencode(".jpg", img)
    png_output = base64.b64encode(im_buf_arr)
    if os.path.exists(f'{config.LOG_DIR}/messages.log'):
        p1 = subprocess.run(['tail', '-100', f'{config.LOG_DIR}/messages.log'], check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log_out = p1.stdout.decode()
    else:
        log_out = '## empty ##'

    return render_template('simulator.html', version=ApiServer.scrabscrap_version,
                           img_data=urllib.parse.quote(png_output),
                           log=log_out)


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
    api.start_server(host='127.0.0.1')

    sleep(240)  # stop after 2 min
    api.stop_server()
    cam_event.set()


if __name__ == '__main__':
    main()
