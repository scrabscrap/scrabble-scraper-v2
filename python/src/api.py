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
import subprocess
import urllib.parse
from time import sleep

import cv2
from flask import (Flask, jsonify, redirect, render_template_string, request,
                   send_from_directory, url_for)
from werkzeug.serving import make_server

from config import config
from game_board.board import overlay_grid
from processing import get_last_warp, warp_image
from threadpool import pool


class ApiServer:
    app = Flask(__name__)
    last_msg = ''
    cam = None
    flask_shutdown_blocked = False
    scrabscrap_version = ''

    @app.get('/')
    def get_defaults():
        return render_template_string(
            '<html><head>'
            '<style>'
            '  .button:not(:last-child) { margin-right: 10px; }'
            '</style>'
            '</head>'
            '<body>'
            '<div class="container">'
            '  <button type="button" onclick="location.href=\'/cam\'">Camera</button>'
            '  <button type="button" onclick="location.href=\'/test_led\'">Test LED</button>'
            '  <button type="button" onclick="location.href=\'/test_display\'">Test display</button>'
            '  <button style="margin-right: 20px;" type="button" onclick="location.href=\'/settings\'">Settings</button>'
            '  <button style="margin-right: 20px;" type="button" onclick="location.href=\'/download_logs\'">'
            '    Download Logs</button>'
            '  <button type="button" onclick="location.href=\'/logs\'">Logs</button>'
            '  <button type="button" onclick="location.href=\'/upgrade_linux\'">Upgrade Linux</button>'
            '  <button type="button" onclick="location.href=\'/upgrade_scrabscrap\'">Upgrade ScrabScrap</button>'
            '  <button type="button" onclick="location.href=\'/shutdown\'">Shutdown</button>'
            '</div><br/>'
            '<form action="/player" method="get"><div>Names</div>'
            '  <input type="text" name="player1" placeholder="Player 1" required>'
            '  <input type="text" name="player2" placeholder="Player 2" required>'
            '  <input type="submit" value="Submit">'
            '</form>'
            '<form action="/settings" method="get"><div>Setting</div>'
            '  <input type="text" name="setting" placeholder="Parameter" required>'
            '  <input type="text" name="value" placeholder="Value">'
            '  <input type="submit" value="Submit">'
            '</form>'
            '<form action="/wifi" method="post"><div>WiFi</div>'
            '  <input type="text" name="ssid" placeholder="ssid" required>'
            '  <input type="password" pattern=".{8,}" name="psk" placeholder="psk" required>'
            '  <input type="submit" value="Submit">'
            '</form>'
            'ScrabScrap version: {{version}}<br/>'
            'last result: <div style="white-space: pre-wrap;">{{message}}</div><br/>'
            '</body></html>', version=ApiServer.scrabscrap_version, message=ApiServer.last_msg)

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
        ApiServer.last_msg = json.dumps(config_as_dict, sort_keys=True, indent=2)
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
            ApiServer.last_msg = json.dumps(config_as_dict, sort_keys=True, indent=2)
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

    @app.post('/wifi')
    def wifi():
        ssid = request.form.get('ssid')
        key = request.form.get('psk')
        logging.debug(f'ssid={ssid}')
        p1 = subprocess.call(f"sudo sh -c 'wpa_passphrase {ssid} {key} >> /etc/wpa_supplicant/wpa_supplicant.conf'", shell=True)
        ApiServer.last_msg = f'set wifi return={p1}'
        return redirect(url_for('get_defaults'))

    @app.route('/cam')
    def get_cam():
        if ApiServer.cam is not None:
            img = ApiServer.cam.read()
            _, im_buf_arr = cv2.imencode(".jpg", img)
            png_output = base64.b64encode(im_buf_arr)
            warped = warp_image(img)
            warp_coord = json.dumps(get_last_warp().tolist())  # type: ignore
            overlay = overlay_grid(warped)
            _, im_buf_arr = cv2.imencode(".jpg", overlay)
            png_overlay = base64.b64encode(im_buf_arr)
        else:
            png_output = ''
            png_overlay = ''
            warp_coord = ''
        ApiServer.last_msg = ''
        return render_template_string(
            '<html><head>'
            '<style>'
            '  .button:not(:last-child) { margin-right: 10px; }'
            '</style>'
            '</head>'
            '<body>'
            '<div class="container">'
            '  <button type="button" onclick="location.href=\'/cam\'">Reload</button>'
            '  <button type="button" onclick="location.href=\'/\'">Back</button>'
            '  <button type="button" onclick="location.href=\'/settings?setting=video.warp_coordinates&value={{warp_coord}}\'">'
            '     Store Warp</button>'
            '  <button type="button" onclick="location.href=\'/settings?setting=video.warp_coordinates&value=\'">'
            '     Clear Warp</button>'
            '</div><br/>'
            '<img style="float: left; padding:5px;max-width: 45vw;max-height: calc(95vh - 50px);" '
            'src="data:image/jpg;base64,{{img_data}}"/>'
            '<img style="padding:5px; max-width: 45vw;max-height: calc(95vh - 50px);" '
            'src="data:image/jpg;base64,{{warp_data}}"/><br/>'
            '</body></html>',
            img_data=urllib.parse.quote(png_output), warp_data=urllib.parse.quote(png_overlay),
            warp_coord=urllib.parse.quote(warp_coord))

    @app.route('/logs')
    def logs():
        ApiServer.last_msg = ''
        if os.path.exists(f'{config.LOG_DIR}/messages.log'):
            p1 = subprocess.run(['tail', '-100', f'{config.LOG_DIR}/messages.log'], check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log_out = p1.stdout.decode()
        else:
            log_out = '## empty ##'
        return render_template_string(
            '<html><head>'
            '<style>'
            '  .button:not(:last-child) { margin-right: 10px; }'
            '</style>'
            '</head>'
            '<body>'
            '<div class="container">'
            '  <button type="button" onclick="location.href=\'/\'">Back</button>'
            '</div><br/>'
            '<div class="container">'
            '  <div style="white-space: pre-wrap;" id="display_list">{{log}}</div>'
            '</div>'
            '</body></html>', log=log_out)

    @app.route('/upgrade_linux')
    def update_linux():
        ApiServer.flask_shutdown_blocked = True
        p1 = subprocess.run(['sudo', 'apt-get', 'update'], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p2 = subprocess.run(['sudo', 'apt-get', 'dist-upgrade', '-y'], check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ApiServer.flask_shutdown_blocked = False
        ApiServer.last_msg = f'{p1.stdout.decode()}\n{p2.stdout.decode()}'
        return redirect(url_for('get_defaults'))

    @app.route('/upgrade_scrabscrap')
    def update_scrabscrap():
        ApiServer.flask_shutdown_blocked = True
        p1 = subprocess.run(['git', 'fetch'], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # TODO: PROD-> git reset --hard origin/main
        p2 = subprocess.run(['git', 'pull'], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ApiServer.flask_shutdown_blocked = False
        ApiServer.last_msg = f'{p1.stdout.decode()}\n{p2.stdout.decode()}'
        version_info = subprocess.run(['git', 'describe', '--tags'], check=False,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if version_info.returncode > 0:
            version_info = subprocess.run(['git', 'rev-parse', 'HEAD'], check=False,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ApiServer.scrabscrap_version = version_info.stdout.decode()
        return redirect(url_for('get_defaults'))

    @app.route('/test_led')
    def test_led():
        from hardware.led import LED, LEDEnum

        ApiServer.flask_shutdown_blocked = True
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
        ApiServer.flask_shutdown_blocked = False
        ApiServer.last_msg = 'led_test ended'
        return redirect(url_for('get_defaults'))

    @app.route('/test_display')
    def test_display():
        from hardware.oled import PlayerDisplay
        from scrabblewatch import ScrabbleWatch

        ApiServer.flask_shutdown_blocked = True
        display = PlayerDisplay()
        watch = ScrabbleWatch(display)
        watch.display.show_boot()
        watch.display.show_cam_err()
        watch.display.show_config()
        watch.display.show_ftp_err()
        watch.display.show_ready()
        watch.display.clear()
        watch.display.show()
        ApiServer.flask_shutdown_blocked = False
        ApiServer.last_msg = 'display_test ended'
        return redirect(url_for('get_defaults'))

    @app.route('/download_logs', methods=['POST', 'GET'])
    def download_logs():
        ApiServer.last_msg = 'download logs'
        return send_from_directory(f'{config.WORK_DIR}', 'log.conf', as_attachment=True)

    # TODO:
    # - [o] download logs / images / games
    # - [ ] shutdown system
    # - [o] upgrade scrabscrap
    # - [x] upgrade linux
    # - [x] test led
    # - [x] test display
    # - [o] set player-names
    # - [x] set wifi
    # - [ ] set move?
    # - [ ] set rack
    # - [ ] get game status
    # - [x] store warp
    # - [x] clear warp

    def start_server(self):
        logging.debug('start api server')
        version_info = subprocess.run(['git', 'describe', '--tags'], check=False,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if version_info.returncode > 0:
            version_info = subprocess.run(['git', 'rev-parse', 'HEAD'], check=False,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ApiServer.scrabscrap_version = version_info.stdout.decode()
        self.app.config['DEBUG'] = False
        self.app.config['TESTING'] = False
        self.server = make_server('0.0.0.0', 5000, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.server.serve_forever()

    def stop_server(self):
        print(f'server shutdown blocked: {ApiServer.flask_shutdown_blocked}')
        while ApiServer.flask_shutdown_blocked:
            sleep(0.1)
        self.server.shutdown()


def main():
    # for testing
    from threading import Event

    from hardware.camera import Camera

    logging.config.fileConfig(fname=config.WORK_DIR + '/log.conf',
                              disable_existing_loggers=False,
                              defaults={'level': 'DEBUG',
                                        'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})

    cam = Camera()
    cam_event = Event()
    _ = pool.submit(cam.update, cam_event)

    api = ApiServer()
    ApiServer.cam = cam  # type: ignore
    pool.submit(api.start_server)

    sleep(240)  # stop after 2 min
    api.stop_server()
    cam_event.set()


if __name__ == '__main__':
    main()
