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
import base64
import json
import logging
import logging.config
import urllib.parse
from threading import Event
from time import sleep

import cv2
from flask import Flask, jsonify, render_template_string, request
from werkzeug.serving import make_server

# TODO: remove before prod
logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')

from config import config
from hardware.camera import Camera
from threadpool import pool

flask_shutdown_blocked = False
cam = None


class ApiServer:
    app = Flask(__name__)

    @app.get('/')
    def get_defaults():
        return render_template_string(
            '<html><head></head>'
            '<body>'
            '<a href="/player">Set Player-Names</a><br/>'
            '<a href="/settings">Set Configuration Parameter</a><br/>'
            '<hr />'
            '<a href="/cam">Camera</a><br/>'
            '<hr />'
            '<a href="/upgrade_linux">Upgrade Linux (requires Internet access)</a><br/>'
            '<a href="/upgrade_scrapscrap">Upgrade ScrabScrap (requires Internet access)</a><br/>'
            '<hr />'
            '<a href="/test_led">Test LEDs</a><br/>'
            '<a href="/test_display">Test Display</a><br/>'
            '<hr />'
            '<a href="/download_logs">Download Logs</a><br/>'
            '<hr />'
            '<a href="/shutdown">Shutdown System</a><br/>'
            '</body></html>')

    @app.get('/settings')
    def get_settings():
        try:
            must_save = False
            for i in request.args.items():
                section, option = str(i[0]).split('.', maxsplit=2)
                value = i[1]
                logging.debug(f'[{section}] {option}={value}')
                if section not in config.config.sections():
                    config.config.add_section(section)
                config.config.set(section, option, str(value))
                must_save = True
        except ValueError:
            return {"error": "Value error in Parameter"}, 415
        if must_save:
            config.save()
        config_as_dict = config.config_as_dict()
        logging.debug(f'{config_as_dict}')
        return jsonify(config_as_dict)

    @app.post('/settings')  # type: ignore
    def add_settings():
        if request.is_json:
            must_save = False
            json_object = request.get_json()
            for section, subdict in json_object.items():  # type: ignore
                for option, value in subdict.items():
                    logging.debug(f'[{section}] {option}={value}')
                    if section not in config.config.sections():
                        config.config.add_section(section)
                    config.config.set(section, option, str(value))
                    must_save = True
            if must_save:
                config.save()
            config_as_dict = config.config_as_dict()
            logging.debug(f'{config_as_dict}')
            return jsonify(config_as_dict), 201
        else:
            return {"error": "Request must be JSON"}, 415

    @app.route('/cam')
    def get_cam():
        # TODO: use live pictures
        # fakecamera_formatter = config.SIMULATE_PATH
        # img = cv2.imread(fakecamera_formatter.format(0))
        if cam is not None:
            img = cam.read()
            _, im_buf_arr = cv2.imencode(".jpg", img)
            png_output = base64.b64encode(im_buf_arr)
        else:
            png_output = ''
        return render_template_string(
            '<html><head><meta http-equiv="refresh" content="2" /></head>'
            '<body>'
            '<img style="max-width: 95vw;max-height: 95vh;'
            '-webkit-box-shadow: 0 0 13px 3px rgba(0,0,0,1);'
            '-moz-box-shadow: 0 0 13px 3px rgba(0,0,0,1);'
            'box-shadow: 0 0 13px 3px rgba(0,0,0,1);" '
            'src="data:image/jpg;base64,{{img_data}}"/>'
            '</body></html>',
            img_data=urllib.parse.quote(png_output))

    @app.route('/upgrade_linux')
    def update_linux():
        import subprocess
        global flask_shutdown_blocked

        flask_shutdown_blocked = True
        p1 = subprocess.run(['sudo', 'apt-get', 'update'], check=True, capture_output=True)
        p2 = subprocess.run(['sudo', 'apt-get', 'dist-upgrade', '-y'], check=True, capture_output=True)
        flask_shutdown_blocked = False
        return {'01-apt-get_update': f'{p1.stdout.decode()} {p1.stderr.decode()}',
                '02-apt-get_dist-upgrade': f'{p2.stdout.decode()} {p2.stderr.decode()}'
                }, 415 if p1.returncode > 0 or p2.returncode > 0 else 201

    @app.route('/upgrade_scrabscrap')
    def update_scrabscrap():
        import subprocess
        global flask_shutdown_blocked

        flask_shutdown_blocked = True
        p1 = subprocess.run(['ls', '-al'], check=True, capture_output=True)
        flask_shutdown_blocked = False
        return {'git_pull': f'{p1.stdout.decode()} {p1.stderr.decode()}',
                }, 415 if p1.returncode > 0 else 201

    @app.route('/test_led')
    def test_led():
        from hardware.led import LED, LEDEnum

        LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        sleep(1)
        LED.switch_on({})  # type: ignore
        sleep(1)
        LED.blink_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        sleep(2)
        LED.blink_on({LEDEnum.yellow})
        sleep(2)
        LED.switch_on({})  # type: ignore
        sleep(1)
        LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
        sleep(1)
        LED.switch_on({LEDEnum.green})
        sleep(1)
        LED.switch_on({LEDEnum.yellow})
        sleep(1)
        LED.switch_on({LEDEnum.red})
        sleep(1)
        LED.switch_on({})  # type: ignore
        return {'led_test': 'ended'}, 201

    @app.route('/test_display')
    def test_display():
        from hardware.oled import PlayerDisplay
        from scrabblewatch import ScrabbleWatch

        display = PlayerDisplay()
        watch = ScrabbleWatch(display)
        watch.display.show_boot()
        watch.display.show_cam_err()
        watch.display.show_config()
        watch.display.show_ftp_err()
        watch.display.show_ready()
        watch.display.clear()
        watch.display.show()
        return {'display_test': 'ended'}, 201

    # TODO:
    # - [ ] download logs / images / games
    # - [ ] shutdown system
    # - [o] upgrade scrabscrap
    # - [x] upgrade linux
    # - [x] test led
    # - [x] test display
    # - [ ] set player-names
    # - [ ] set move?
    # - [ ] set rack
    # - [ ] get game status

    def start_server(self):
        logging.debug('try to start server')
        self.server = make_server('0.0.0.0', 5000, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.server.serve_forever()

    def stop_server(self):
        print(f'server shutdown blocked: {flask_shutdown_blocked}')
        while flask_shutdown_blocked:
            sleep(0.1)
        self.server.shutdown()


def test_json():
    value = '{"board":{"layout":"custom"},"button":{"hold1":"3"},"development":{},"hallo":{"test":"value"},'
    '"hugo":{"test":"test"},"input":{"keyboard_wait":"False"},"motion":{},"output":{"ftp":"False"},'
    '"scrabble":{},"system":{"quit":"exit"},"video":{"rotade":"False"}}'

    json_object = json.loads(value)
    print(f'{json_object} type {type(json_object)}')
    for majorkey, subdict in json_object.items():
        for subkey, value in subdict.items():
            print(f'[{majorkey}] {subkey}={value}')


def main():
    global cam

    cam = Camera()
    # cam = MockCamera()
    cam_event = Event()
    _ = pool.submit(cam.update, cam_event)

    api = ApiServer()
    pool.submit(api.start_server)
    sleep(120)
    api.stop_server()
    cam_event.set()


if __name__ == '__main__':
    main()
    # test_json()
