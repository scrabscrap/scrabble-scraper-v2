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
import os
import urllib.parse
from threading import Event
from time import sleep

import cv2
from flask import (Flask, jsonify, redirect, render_template_string, request,
                   send_from_directory, url_for)
from werkzeug.serving import make_server

# TODO: remove before prod
logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')

from config import config
from hardware.camera import Camera
from threadpool import pool

flask_shutdown_blocked = False
cam = None
ROOT_PATH = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../work')


class ApiServer:
    app = Flask(__name__)
    last_msg = ''

    @app.get('/')
    def get_defaults():
        # TODO: Status Informationen ergänzen
        return render_template_string(
            '<html><head></head>'
            '<body>'
            'last result: <pre>{{message}}</pre><br/>'
            '<form action="/player" method="get">Names'
            '  <input type="text" name="player1" placeholder="Player 1">'
            '  <input type="text" name="player2" placeholder="Player 2">'
            '  <input type="submit" value="Submit">'
            '</form>'
            '<form action="/settings" method="get">Setting'
            '  <input type="text" name="setting" placeholder="Parameter">'
            '  <input type="text" name="value" placeholder="Value">'
            '  <input type="submit" value="Submit">'
            '</form>'

            '<button type="button" onclick="location.href=\'/cam\'">Camera</button>'
            '<button type="button" onclick="location.href=\'/test_led\'">Test LED</button>'
            '<button type="button" onclick="location.href=\'/test_display\'">Test display</button>'
            '<br/><br/>'
            '<button type="button" onclick="location.href=\'/download_logs\'">Download Logs</button>'
            '<br/><br/>'
            '<button type="button" onclick="location.href=\'/upgrade_linux\'">Upgrade Linux</button>'
            '<button type="button" onclick="location.href=\'/upgrade_scrabscrap\'">Upgrade ScrabScrap</button>'
            '<button type="button" onclick="location.href=\'/shutdown\'">Shutdown</button>'
            '</body></html>', message=ApiServer.last_msg)

    @app.get('/settings')
    def get_settings():
        try:
            must_save = False
            for i in request.args.items():
                if request.args.get('setting') is None:
                    path = i[0]
                    value = i[1]
                else:
                    path = request.args.get('setting')
                    value = request.args.get('value')
                section, option = str(path).split('.', maxsplit=2)
                logging.debug(f'[{section}] {option}={value}')
                if section not in config.config.sections():
                    config.config.add_section(section)
                config.config.set(section, option, str(value))
                logging.debug(f'{section}.{option}={value}')
                must_save = True
        except ValueError:
            logging.error(f'Error on settings: {request.args.items()}')
            ApiServer.last_msg = 'error: Value error in Parameter'
            return redirect(url_for('get_defaults'))
        if must_save:
            config.save()
        config_as_dict = config.config_as_dict()
        logging.debug(f'{config_as_dict}')
        ApiServer.last_msg = f'{config_as_dict}'
        return redirect(url_for('get_defaults'))

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
            ApiServer.last_msg = 'json api'
            return jsonify(config_as_dict), 201
        else:
            return {'error': 'Request must be JSON'}, 415

    @app.route('/player')  # type: ignore
    def player():
        player1 = request.args.get('player1')
        player2 = request.args.get('player2')
        logging.debug(f'player1={player1} player2={player2}')
        ApiServer.last_msg = f'player1={player1}\nplayer2={player2}'
        return redirect(url_for('get_defaults'))

    @app.route('/cam')
    def get_cam():
        # fakecamera_formatter = config.SIMULATE_PATH
        # img = cv2.imread(fakecamera_formatter.format(0))
        if cam is not None:
            img = cam.read()
            _, im_buf_arr = cv2.imencode(".jpg", img)
            png_output = base64.b64encode(im_buf_arr)
        else:
            png_output = ''
        ApiServer.last_msg = ''
        return render_template_string(
            '<html><head></head>'
            '<body>'
            '<button type="button" onclick="location.href=\'/cam\'">Reload</button>'
            '<button type="button" onclick="location.href=\'/\'">Back</button><br/><br/>'
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
        ApiServer.last_msg = f'{p1.stdout.decode()} {p1.stderr.decode()}{p2.stdout.decode()} {p2.stderr.decode()}'
        return redirect(url_for('get_defaults'))

    @app.route('/upgrade_scrabscrap')
    def update_scrabscrap():
        import subprocess
        global flask_shutdown_blocked

        flask_shutdown_blocked = True
        p1 = subprocess.run(['ls', '-al'], check=True, capture_output=True)
        flask_shutdown_blocked = False
        ApiServer.last_msg = f'{p1.stdout.decode()} {p1.stderr.decode()}'
        return redirect(url_for('get_defaults'))

    @app.route('/test_led')
    def test_led():
        from hardware.led import LED, LEDEnum
        global flask_shutdown_blocked

        flask_shutdown_blocked = True
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
        flask_shutdown_blocked = False
        ApiServer.last_msg = 'led_test ended'
        return redirect(url_for('get_defaults'))

    @app.route('/test_display')
    def test_display():
        from hardware.oled import PlayerDisplay
        from scrabblewatch import ScrabbleWatch
        global flask_shutdown_blocked

        flask_shutdown_blocked = True
        display = PlayerDisplay()
        watch = ScrabbleWatch(display)
        watch.display.show_boot()
        watch.display.show_cam_err()
        watch.display.show_config()
        watch.display.show_ftp_err()
        watch.display.show_ready()
        watch.display.clear()
        watch.display.show()
        flask_shutdown_blocked = False
        ApiServer.last_msg = 'display_test ended'
        return redirect(url_for('get_defaults'))

    @app.route('/download_logs', methods=['POST', 'GET'])
    def download_logs():
        ApiServer.last_msg = 'download logs'
        return send_from_directory(f'{ROOT_PATH}', 'log.conf', as_attachment=True)

    # TODO:
    # - [o] download logs / images / games
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
