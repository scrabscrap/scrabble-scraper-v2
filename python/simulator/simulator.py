import logging
import logging.config
import os
from time import sleep

from api_server_thread import ApiServer
from config import config
from flask import render_template
from threadpool import pool

TEMPLATE_FOLDER = f'{os.path.dirname(__file__) or "."}/../src/templates'
STATIC_FOLDER = f'{os.path.dirname(__file__) or "."}/../src/static'


def simulator() -> str:
    return render_template('simulator.html', version=ApiServer.scrabscrap_version)


def main():
    from threading import Event
    from hardware.camera_thread import Camera, CameraEnum
    
    logging.config.fileConfig(fname=config.WORK_DIR + '/log.conf',
                              disable_existing_loggers=False,
                              defaults={'level': 'DEBUG',
                                        'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})

    cam = Camera(useCamera=CameraEnum.FILE)
    cam_event = Event()
    _ = pool.submit(cam.update, cam_event)

    api = ApiServer()
    ApiServer.cam = cam  # type: ignore
    # api.app.config['TEMPLATE_FOLDER'] = TEMPLATE_FOLDER
    # api.app.config['STATIC_FOLDER'] = STATIC_FOLDER
    api.app.add_url_rule('/simulator', 'simulator', simulator)
    api.start_server()

    sleep(240)  # stop after 2 min
    api.stop_server()
    cam_event.set()


if __name__ == '__main__':
    main()
