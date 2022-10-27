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
import json
import logging
import logging.config
import os
import subprocess
import urllib.parse
from time import sleep

import cv2
import numpy as np
from flask import (Flask, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)
from werkzeug.serving import make_server

from config import config
from game_board.board import overlay_grid
from processing import get_last_warp, warp_image
from state import State
from threadpool import pool


class ApiServer:
    """ definition of flask server """
    app = Flask(__name__)
    last_msg = ''
    cam = None
    flask_shutdown_blocked = False
    scrabscrap_version = ''

    @staticmethod
    @app.get('/')
    @app.get('/index')
    def get_defaults():
        """ index web page """

        (player1, player2) = State().game.nicknames
        return render_template('index.html', version=ApiServer.scrabscrap_version, message=ApiServer.last_msg,
                               player1=player1, player2=player2)

    @staticmethod
    @app.get('/settings')
    def get_settings():
        """display settings on web page"""
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
                if value is not None and value != '':
                    if section not in config.config.sections():
                        config.config.add_section(section)
                    config.config.set(section, option, str(value))
                    logging.debug(f'{section}.{option}={value}')
                else:
                    config.config.remove_option(section, option)
                    logging.debug(f'delete {section}.{option}')
                must_save = True
        except ValueError:
            logging.error(f'Error on settings: {request.args.items()}')
            ApiServer.last_msg = 'error: Value error in Parameter'
            return render_template('settings.html', version=ApiServer.scrabscrap_version, message=ApiServer.last_msg)
        if must_save:
            config.save()
        config_as_dict = config.config_as_dict()
        ApiServer.last_msg = json.dumps(config_as_dict, sort_keys=False, indent=2, ensure_ascii=False)
        return render_template('settings.html', version=ApiServer.scrabscrap_version, message=ApiServer.last_msg)

    @staticmethod
    @app.post('/settings')  # type: ignore
    def add_settings():
        """ post request to add settings via json"""
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
        return {'error': 'Request must be JSON'}, 415

    @staticmethod
    @app.route('/player')  # type: ignore
    def player():
        """ set player names """

        player1 = request.args.get('player1')
        player2 = request.args.get('player2')
        logging.debug(f'player1={player1} player2={player2}')
        # state holds the current game
        State().game.nicknames = (player1, player2)
        ApiServer.last_msg = f'player1={player1}\nplayer2={player2}'
        return redirect(url_for('get_defaults'))

    @staticmethod
    @app.post('/wifi')
    def post_wifi():
        """ set wifi param (ssid, psk) via post request """
        ssid = request.form.get('ssid')
        key = request.form.get('psk')
        logging.debug(f'ssid={ssid}')
        process = subprocess.call(
            f"sudo sh -c 'wpa_passphrase {ssid} {key} >> /etc/wpa_supplicant/wpa_supplicant.conf'", shell=True)
        ApiServer.last_msg = f'set wifi return={process}'
        return render_template('wifi.html', version=ApiServer.scrabscrap_version, message=ApiServer.last_msg)

    @staticmethod
    @app.get('/wifi')
    def get_wifi():
        """ display wifi web page """
        ApiServer.last_msg = ''
        return render_template('wifi.html', version=ApiServer.scrabscrap_version, message=ApiServer.last_msg)

    @staticmethod
    @app.route('/scan_wifi')
    def scan_wifi():
        """ start wifi scan process """
        process1 = subprocess.run(['wpa_cli', 'list_networks', '-i', 'wlan0'], check=False,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        _ = subprocess.run(['wpa_cli', 'scan', '-i', 'wlan0'], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        sleep(1)
        process2 = subprocess.run(['wpa_cli', 'scan_results', '-i', 'wlan0'], check=False,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ApiServer.last_msg = f'wifi config\n{process1.stdout.decode()}\nwifi search\n{process2.stdout.decode()}'
        logging.debug(ApiServer.last_msg)
        return render_template('wifi.html', version=ApiServer.scrabscrap_version, message=ApiServer.last_msg)

    @staticmethod
    @app.route('/cam')
    def get_cam():
        """ display current camera picture """

        logging.debug(f'request args {request.args.keys()}')
        if len(request.args.keys()) > 0:
            coord = list(request.args.keys())[0]
            col: int = int(coord.split(',')[0])
            row: int = int(coord.split(',')[1])
            logging.debug(f'coord x:{col} y:{row}')
            rect = np.array(config.warp_coordinates, dtype="float32")
            if col < 200 and row < 200:
                rect[0] = (col, row)
            elif col < 200:
                rect[1] = (col, row)
            elif row < 200:
                rect[3] = (col, row)
            else:
                rect[2] = (col, row)
            logging.debug(f"new warp: {np.array2string(rect, formatter={'float_kind':lambda x: '%.1f' % x}, separator=', ')}")
            config.config.set('video', 'warp_coordinates', np.array2string(
                rect, formatter={'float_kind': lambda x: '%.1f' % x}, separator=','))
        warp_coord_cnf = str(config.warp_coordinates)
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
        return render_template('cam.html', version=ApiServer.scrabscrap_version,
                               img_data=urllib.parse.quote(png_output), warp_data=urllib.parse.quote(png_overlay),
                               warp_coord=urllib.parse.quote(warp_coord), warp_coord_raw=warp_coord,
                               warp_coord_cnf=warp_coord_cnf)

    @staticmethod
    @app.route('/logs')
    def logs():
        """ display message log """
        ApiServer.last_msg = ''
        if os.path.exists(f'{config.log_dir}/messages.log'):
            process = subprocess.run(['tail', '-100', f'{config.log_dir}/messages.log'], check=True,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log_out = process.stdout.decode()
        else:
            log_out = '## empty ##'
        return render_template('logs.html', log=log_out)

    @staticmethod
    @app.route('/upgrade_linux')
    def update_linux():
        """ start linux upgrade """

        if State().current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            process1 = subprocess.run(['sudo', 'apt-get', 'update'], check=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            process2 = subprocess.run(['sudo', 'apt-get', 'dist-upgrade', '-y'], check=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            ApiServer.flask_shutdown_blocked = False
            ApiServer.last_msg = f'{process1.stdout.decode()}\n{process2.stdout.decode()}'
            logging.debug(ApiServer.last_msg)
        else:
            ApiServer.last_msg = 'not in State START'
        return redirect(url_for('get_defaults'))

    @staticmethod
    @app.route('/upgrade_scrabscrap')
    def update_scrabscrap():
        """ start scrabscrap upgrade """

        if State().current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            process1 = subprocess.run(['git', 'fetch'], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # TODO: git checkout v2 --hard v2
            process2 = subprocess.run(['git', 'pull', '--autostash'], check=False,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            process3 = subprocess.run(['git', 'gc'], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            ApiServer.flask_shutdown_blocked = False
            ApiServer.last_msg = f'{process1.stdout.decode()}\n{process2.stdout.decode()}\n{process3.stdout.decode()}'
            logging.debug(ApiServer.last_msg)
            version_info = subprocess.run(['git', 'describe', '--tags'], check=False,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if version_info.returncode > 0:
                version_info = subprocess.run(['git', 'rev-parse', 'HEAD'], check=False,
                                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            ApiServer.scrabscrap_version = version_info.stdout.decode()
        else:
            ApiServer.last_msg = 'not in State START'
        return redirect(url_for('get_defaults'))

    @staticmethod
    @app.route('/test_led')
    def test_led():
        """ start simple led test """
        from hardware.led import LED, LEDEnum

        if State().current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
            logging.debug('LED switch on red yellow green')
            sleep(1)
            LED.switch_on({})  # type: ignore
            sleep(1)
            LED.blink_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
            logging.debug('LED blink on red yellow green')
            sleep(2)
            LED.blink_on({LEDEnum.yellow})
            logging.debug('LED blink on yellow')
            sleep(2)
            LED.switch_on({})  # type: ignore
            sleep(1)
            LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
            logging.debug('LED switch on red yellow green')
            sleep(1)
            LED.switch_on({LEDEnum.green})
            logging.debug('LED switch on green')
            sleep(1)
            LED.switch_on({LEDEnum.yellow})
            logging.debug('LED switch on yellow')
            sleep(1)
            LED.switch_on({LEDEnum.red})
            logging.debug('LED switch on red')
            sleep(1)
            LED.switch_on({})  # type: ignore
            ApiServer.flask_shutdown_blocked = False
            ApiServer.last_msg = 'led_test ended'
        else:
            ApiServer.last_msg = 'not in State START'
        return redirect(url_for('get_defaults'))

    @staticmethod
    @app.route('/test_display')
    def test_display():
        """ start simple display test """
        try:
            from hardware.oled import PlayerDisplay
        except ImportError:
            logging.warning('use mock as PlayerDisplay')
            from display import Display as PlayerDisplay
        from scrabblewatch import ScrabbleWatch

        if State().current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            display = PlayerDisplay()
            watch = ScrabbleWatch(display)
            watch.display.show_boot()
            logging.debug('Display show boot')
            sleep(0.5)
            watch.display.show_cam_err()
            logging.debug('Display show cam err')
            sleep(0.5)
            watch.display.show_config()
            logging.debug('Display show config')
            sleep(0.5)
            watch.display.show_ftp_err()
            logging.debug('Display show ftp err')
            sleep(0.5)
            watch.display.show_ready()
            logging.debug('Display show ready')
            sleep(0.5)
            watch.display.clear()
            logging.debug('Display clear display')
            watch.display.show()
            ApiServer.flask_shutdown_blocked = False
            ApiServer.last_msg = 'display_test ended'
        else:
            ApiServer.last_msg = 'not in State START'
        return redirect(url_for('get_defaults'))

    @staticmethod
    @app.route('/download_logs', methods=['POST', 'GET'])
    def download_logs():
        """ download message log """
        ApiServer.last_msg = 'download logs'
        return send_from_directory(f'{config.work_dir}', 'log.conf', as_attachment=True)

    @staticmethod
    @app.route('/game_status', methods=['POST', 'GET'])
    def game_status():
        """ get request to current game state """

        return State().game.json_str(), 201

    def start_server(self, host: str = '0.0.0.0', port=5050):
        """ start flask server """
        logging.debug('start api server')
        # flask log only error
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        version_info = subprocess.run(['git', 'describe', '--tags'], check=False,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if version_info.returncode > 0:
            version_info = subprocess.run(['git', 'rev-parse', 'HEAD'], check=False,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ApiServer.scrabscrap_version = version_info.stdout.decode()
        self.app.config['DEBUG'] = False
        self.app.config['TESTING'] = False
        self.server = make_server(host=host, port=port, app=self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.server.serve_forever()

    def stop_server(self):
        """ stop flask server """
        logging.info(f'server shutdown blocked: {ApiServer.flask_shutdown_blocked}')
        while ApiServer.flask_shutdown_blocked:
            sleep(0.1)
        self.server.shutdown()


def main():
    """ main for standalone test """
    # for testing
    from threading import Event
    from hardware.camera_thread import Camera

    logging.config.fileConfig(fname=config.work_dir + '/log.conf',
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
