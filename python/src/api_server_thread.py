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
import configparser
import json
import logging
import logging.config
import os
import re
import subprocess
import urllib.parse
from io import StringIO
from signal import alarm
from time import sleep

import cv2
import netifaces
import numpy as np
from flask import (Flask, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_sock import Sock
from werkzeug.serving import make_server

from config import config
from game_board.board import overlay_grid
from processing import (get_last_warp, recalculate_score_on_admin_change,
                        warp_image)
from state import State
from threadpool import pool


class ApiServer:  # pylint: disable=R0904 # too many public methods
    """ definition of flask server """
    app = Flask(__name__)
    sock = Sock(app)
    last_msg = ''
    cam = None
    flask_shutdown_blocked = False
    scrabscrap_version = ''
    simulator = False
    local_webapp = False

    def __init__(self, cam=None) -> None:
        if cam:
            ApiServer.cam = cam

    @staticmethod
    @app.route('/webapp/<path:path>')
    def static_file(path):
        """static routing for web app on rpi"""
        return ApiServer.app.send_static_file(f'webapp/{path}')

    @staticmethod
    @app.get('/')
    @app.get('/index')
    def get_defaults():
        """ index web page """
        (player1, player2) = State().game.nicknames
        tournament = config.tournament
        return render_template('index.html', apiserver=ApiServer, player1=player1, player2=player2, tournament=tournament)

    @staticmethod
    @app.get('/edit_moves')
    def edit_moves():
        """ edit moves """
        game = State().game
        return render_template('editmove.html', apiserver=ApiServer, move_list=game.moves)

    @staticmethod
    @app.post('/edit_move')  # type: ignore
    def edit_move():
        """correct game moves"""
        data = request.form
        logging.info(f'{data}')
        move_number = int(request.form.get('move.move'))  # type: ignore
        # player = request.form.get('move.player')
        move_type = request.form.get('move.type')
        coord = request.form.get('move.coord')
        word = request.form.get('move.word')
        word = word.upper().replace(' ', '_') if word else ''
        game = State().game
        logging.debug(f'len moves {len(game.moves)}')
        move = game.moves[move_number - 1]
        vert, col, row = move.calc_coord(coord)  # type: ignore
        if str(move.type.name) != move_type or move.coord != (col, row) or move.word != word or move.is_vertical != vert:
            logging.info(
                f'move edit: move: {move_number} player: {move.player}\n{move.type.name}->{move_type}\n'
                f'{move.is_vertical}->{vert}\n{move.coord}->{(col, row)}\n{move.word}->{word}')  # type: ignore
            if move_type == 'EXCHANGE':
                ApiServer.last_msg = f'try to correct move #{move_number} to exchange'
                logging.debug(f'{ApiServer.last_msg}')
                recalculate_score_on_admin_change(game, int(move_number), (0, 0), True, '')
            elif re.compile('[A-Z_\\.]+').match(word):
                ApiServer.last_msg = f'try to correct move {move_number} {move.get_coord()}: {move.word} to {coord}:{word}'
                logging.debug(f'{ApiServer.last_msg}')
                recalculate_score_on_admin_change(game, int(move_number), (col, row), vert, word)
            else:
                ApiServer.last_msg = f'invalid character in word {word}'
                logging.debug(f'{ApiServer.last_msg}')
        else:
            ApiServer.last_msg = ' no changes detected'
            logging.debug(f'{ApiServer.last_msg}')
        return redirect(url_for('edit_moves'))

    @staticmethod
    @app.post('/insert_move')  # type: ignore
    def insert_move():
        """insert a new move"""
        data = request.form
        logging.info(f'{data}')
        ApiServer.last_msg = 'insert move not supported'
        logging.debug(f'{ApiServer.last_msg}')
        return redirect(url_for('edit_moves'))

    @staticmethod
    @app.get('/settings')
    def get_settings():
        """display settings on web page"""
        try:
            must_save = False
            for i in request.args.items():
                path = request.args.get('setting') or i[0]
                value = request.args.get('value') or i[1]
                section, option = str(path).split('.', maxsplit=2)
                if value is not None and value != '':
                    if value.lower() == 'true':
                        value = 'True'
                    if value.lower() == 'false':
                        value = 'False'
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
            return render_template('settings.html', apiserver=ApiServer)
        if must_save:
            config.save()
        out = StringIO()
        config.config.write(out)
        ApiServer.last_msg = f'{out.getvalue()}'
        return render_template('settings.html', apiserver=ApiServer)

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
    @app.route('/tournament')  # type: ignore
    def tournament():
        """ set tournament """
        tournament = request.args.get('tournament')
        logging.debug(f'tournament={tournament}')
        # state holds the current game
        if tournament is not None:
            if 'tournament' not in config.config.sections():
                config.config.add_section('tournament')
            config.config.set('scrabble', 'tournament', str(tournament))
            config.save()
            ApiServer.last_msg = f'set tournament={tournament}'
        else:
            ApiServer.last_msg = f'can not set: tournament={tournament}'
        return redirect(url_for('get_defaults'))

    @staticmethod
    @app.route('/player')  # type: ignore
    def player():
        """ set player names """
        player1 = request.args.get('player1')
        player2 = request.args.get('player2')
        logging.debug(f'player1={player1} player2={player2}')
        # state holds the current game
        if player1 is not None and player2 is not None:
            State().do_new_player_names(player1, player2)
            ApiServer.last_msg = f'player1={player1}\nplayer2={player2}'
        else:
            ApiServer.last_msg = f'can not set: player1={player1}\nplayer2={player2}'
        return redirect(url_for('get_defaults'))

    @ staticmethod
    @ app.post('/wifi')
    def post_wifi():
        """ set wifi param (ssid, psk) via post request """
        ssid = request.form.get('ssid')
        key = request.form.get('psk')
        logging.debug(
            f"sudo -n sh -c 'wpa_passphrase {ssid} *** | sed \"/^.*ssid=.*/i priority=10\""
            " >> /etc/wpa_supplicant/wpa_supplicant-wlan0.conf'")
        process = subprocess.call(
            f"sudo -n sh -c 'wpa_passphrase {ssid} {key} | sed \"/^.*ssid=.*/i priority=10\""
            " >> /etc/wpa_supplicant/wpa_supplicant-wlan0.conf'", shell=True)
        process1 = subprocess.call(
            "sudo -n /usr/sbin/wpa_cli reconfigure -i wlan0", shell=True)
        ApiServer.last_msg = f'configure wifi return={process}\nreconfigure wpa return={process1}'
        logging.debug(ApiServer.last_msg)
        return redirect(url_for('get_wifi'))

    @ staticmethod
    @ app.get('/wifi')
    def get_wifi():
        """ display wifi web page """
        process1 = subprocess.run(['sudo', '-n', '/usr/sbin/wpa_cli', 'list_networks', '-i', 'wlan0'], check=False,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        wifi_raw = process1.stdout.decode().split(sep='\n')[1:-1]
        wifi_list = [element.split(sep='\t') for element in wifi_raw]
        return render_template('wifi.html', apiserver=ApiServer, wifi_list=wifi_list)

    @ staticmethod
    @ app.post('/delete_wifi')
    def delete_wifi():
        """ delete a wifi entry """
        for i in request.form.keys():
            if request.form.get(i) == 'on':
                logging.debug(f'wpa network delete {i}')
                _ = subprocess.call(
                    f"sudo -n /usr/sbin/wpa_cli remove_network {i} -i wlan0", shell=True)
            _ = subprocess.call(
                "sudo -n /usr/sbin/wpa_cli save_config -i wlan0", shell=True)
        return redirect(url_for('get_wifi'))

    @ staticmethod
    @ app.post('/select_wifi')
    def select_wifi():
        """ select a wifi entry """
        for i in request.form.keys():
            logging.debug(f'wpa network select {i}')
            _ = subprocess.call(
                f"sudo -n /usr/sbin/wpa_cli select_network {i} -i wlan0", shell=True)
        return redirect(url_for('get_wifi'))

    @ staticmethod
    @ app.route('/scan_wifi')
    def scan_wifi():
        """ start wifi scan process """
        _ = subprocess.run(['sudo', '-n', '/usr/sbin/wpa_cli', 'scan', '-i', 'wlan0'], check=False,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        sleep(3)
        process2 = subprocess.run(['sudo', '-n', '/usr/sbin/wpa_cli', 'scan_results', '-i', 'wlan0'], check=False,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ApiServer.last_msg = f'{process2.stdout.decode()}'
        logging.debug(ApiServer.last_msg)
        return redirect(url_for('get_wifi'))

    @ staticmethod
    @ app.route('/cam/clearwarp')
    def cam_clear_warp():
        """clear warp configuration"""
        logging.debug('clear warp')
        config.config.remove_option('video', 'warp_coordinates')
        return redirect(url_for('get_cam'))

    @ staticmethod
    @ app.route('/cam')
    def get_cam():
        """ display current camera picture """
        logging.debug(f'request args {request.args.keys()}')
        if len(request.args.keys()) > 0:
            coord = list(request.args.keys())[0]
            col: int = int(coord.split(',')[0])
            row: int = int(coord.split(',')[1])
            logging.debug(f'coord x:{col} y:{row}')
            rect = get_last_warp()
            if rect is None:
                rect = np.array([
                    [0, 0],
                    [config.video_width, 0],
                    [config.video_width, config.video_height],
                    [0, config.video_height]], dtype="float32")
            if col < 200 and row < 200:
                rect[0] = (col, row)
            elif row < 200:
                rect[1] = (col, row)
            elif col < 200:
                rect[3] = (col, row)
            else:
                rect[2] = (col, row)
            logging.debug(f"new warp: {np.array2string(rect, formatter={'float_kind':lambda x: f'{x:.1f}'}, separator=', ')}")
            config.config.set('video', 'warp_coordinates', np.array2string(
                rect, formatter={'float_kind': lambda x: f'{x:.1f}'}, separator=','))
        warp_coord_cnf = str(config.video_warp_coordinates)
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
        return render_template('cam.html', apiserver=ApiServer,
                               img_data=urllib.parse.quote(png_output), warp_data=urllib.parse.quote(png_overlay),
                               warp_coord=urllib.parse.quote(warp_coord), warp_coord_raw=warp_coord,
                               warp_coord_cnf=warp_coord_cnf)

    @ staticmethod
    @ app.route('/loglevel')
    def loglevel():
        """ settings loglevel, recording """
        loglevel = logging.getLogger('root').getEffectiveLevel()
        return render_template('loglevel.html', apiserver=ApiServer, recording=f'{config.development_recording}',
                               loglevel=f'{loglevel}')

    @ staticmethod
    @ app.post('/set_loglevel')
    def set_loglevel():
        """ set log level / development recording """
        try:
            if 'loglevel' in request.form.keys():
                new_level = int(request.form.get('loglevel'))  # type: ignore
                root_logger = logging.getLogger('root')
                prev_level = root_logger.getEffectiveLevel()
                if new_level != prev_level:
                    logging.warning(f'loglevel changed to {logging.getLevelName(new_level)}')
                    root_logger.setLevel(new_level)
                    log_config = configparser.ConfigParser()
                    with open(f'{config.work_dir}/log.conf', 'r', encoding="UTF-8") as config_file:
                        log_config.read_file(config_file)
                        if 'logger_root' not in log_config.sections():
                            log_config.add_section('logger_root')
                        log_config.set('logger_root', 'level', logging.getLevelName(new_level))
                    with open(f'{config.work_dir}/log.conf', 'w', encoding="UTF-8") as config_file:
                        log_config.write(config_file)

            recording = 'recording' in request.form.keys()
            if config.development_recording != recording:
                logging.debug(f'development.recording changed to {recording}')
                if 'development' not in config.config.sections():
                    config.config.add_section('development')
                config.config.set('development', 'recording', str(recording))
                config.save()
        except IOError as oops:
            ApiServer.last_msg = f'I/O error({oops.errno}): {oops.strerror}'
            return redirect(url_for('/'))
        return redirect(url_for('loglevel'))

    @ staticmethod
    @ app.route('/logentry')
    def logentry():
        process = subprocess.run(['tail', '-100', f'{config.log_dir}/messages.log'], check=False,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log_out = process.stdout.decode()
        return log_out

    @ staticmethod
    @ app.route('/logs')
    def logs():
        """ display message log """
        ApiServer.last_msg = ''
        if os.path.exists(f'{config.log_dir}/messages.log'):
            process = subprocess.run(['tail', '-100', f'{config.log_dir}/messages.log'], check=False,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log_out = process.stdout.decode()
        else:
            log_out = '## empty ##'
        return render_template('logs.html', apiserver=ApiServer, log=log_out)

    @ staticmethod
    @ app.route('/download_logs', methods=['POST', 'GET'])
    def download_logs():
        """ download message logs """
        from zipfile import ZipFile

        with ZipFile(f'{config.log_dir}/log.zip', 'w') as _zip:
            files = ['game.log', 'messages.log']
            for filename in files:
                if os.path.exists(f'{config.log_dir}/{filename}'):
                    _zip.write(f'{config.log_dir}/{filename}')
        ApiServer.last_msg = 'download logs'
        return send_from_directory(f'{config.log_dir}', 'log.zip', as_attachment=True)

    @ staticmethod
    @ app.route('/delete_logs', methods=['POST', 'GET'])
    def delete_logs():
        """ delete message logs """
        import glob
        logging.debug(f'path {config.log_dir}')
        ignore_list = [f'{config.log_dir}/messages.log', f'{config.log_dir}/game.log']
        file_list = glob.glob(f'{config.log_dir}/*')
        file_list = [f for f in file_list if f not in ignore_list]
        # Iterate over the list of filepaths & remove each file.
        for file_path in file_list:
            try:
                os.remove(file_path)
                ApiServer.last_msg += f'delete: {file_path}\n'
            except OSError:
                ApiServer.last_msg += f'error: {file_path}\n'
        for filename in ignore_list:
            with open(filename, 'w', encoding='UTF-8'):
                pass  # empty log file
        logging.debug(ApiServer.last_msg)
        return redirect(url_for('get_defaults'))

    @ staticmethod
    @ app.route('/download_recording', methods=['POST', 'GET'])
    def download_recording():
        """ download recordings """
        import glob
        from zipfile import ZipFile

        with ZipFile(f'{config.work_dir}/recording/recording.zip', 'w') as _zip:
            ignore_list = [f'{config.work_dir}/recording/recording.zip']
            file_list = glob.glob(f'{config.work_dir}/recording/*')
            file_list = [f for f in file_list if f not in ignore_list]
            for filename in file_list:
                _zip.write(f'{filename}')
        ApiServer.last_msg = 'download recording'
        return send_from_directory(f'{config.work_dir}/recording', 'recording.zip', as_attachment=True)

    @ staticmethod
    @ app.route('/delete_recording', methods=['POST', 'GET'])
    def delete_recording():
        """ delete recording(s) """
        import glob
        logging.debug(f'path {config.work_dir}/recording')
        ignore_list = [f'{config.work_dir}/recording/gameRecording.log']
        file_list = glob.glob(f'{config.work_dir}/recording/*')
        file_list = [f for f in file_list if f not in ignore_list]
        # Iterate over the list of filepaths & remove each file.
        for file_path in file_list:
            try:
                os.remove(file_path)
                ApiServer.last_msg += f'delete: {file_path}\n'
            except OSError:
                ApiServer.last_msg += f'error: {file_path}\n'
        with open(f'{config.work_dir}/recording/gameRecording.log', 'w', encoding='UTF-8'):
            pass  # empty log file
        logging.debug(ApiServer.last_msg)
        return redirect(url_for('get_defaults'))

    @ staticmethod
    @ app.route('/upgrade_scrabscrap')
    def update_scrabscrap():
        """ start scrabscrap upgrade """
        if State().current_state == 'START':
            os.system(f'{config.src_dir}/../../scripts/upgrade.sh {config.system_gitbranch} |'
                      f' tee -a {config.log_dir}/messages.log &')
            return redirect(url_for('logs'))
        else:
            ApiServer.last_msg = 'not in State START'
            return redirect(url_for('get_defaults'))

    @ staticmethod
    @ app.route('/test_ftp')
    def test_ftp():
        """ is ftp accessible  """
        import ftplib

        ApiServer.last_msg = 'test ftp config entries\n'
        cfg = configparser.ConfigParser()
        try:
            with open(f'{config.work_dir}/ftp-secret.ini', 'r', encoding="UTF-8") as config_file:
                cfg.read_file(config_file)
        except IOError as err:
            ApiServer.last_msg += f'can not read ftp INI-File {err}\n'
        ApiServer.last_msg += f"ftp-server={cfg.get('ftp', 'ftp-server', fallback='')}\n"
        ApiServer.last_msg += f"ftp-user={cfg.get('ftp', 'ftp-user', fallback='')}\n"
        if cfg.get('ftp', 'ftp-password', fallback=None):
            ApiServer.last_msg += "password found\n"
            try:
                with ftplib.FTP(cfg.get('ftp', 'ftp-server', fallback=''),
                                cfg.get('ftp', 'ftp-user', fallback=''),
                                cfg.get('ftp', 'ftp-password', fallback='')) as session:
                    with open(f'{config.work_dir}/scrabble.ini', 'rb') as file:
                        session.storbinary('STOR scrabble.ini', file)  # send the file
                    ApiServer.last_msg += "upload successful\n"
            except IOError as err:
                ApiServer.last_msg += f'ftp: upload failure {err}\n'
        else:
            ApiServer.last_msg += "no password found\n"
        return redirect(url_for('get_defaults'))

    @ staticmethod
    @ app.route('/test_led')
    def test_led():
        """ start simple led test """
        from hardware.led import LED, LEDEnum

        if State().current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
            logging.debug('LED switch on red yellow green')
            sleep(1)
            LED.blink_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
            logging.debug('LED blink on red yellow green')
            sleep(2)
            LED.switch_on({LEDEnum.green})
            logging.debug('LED switch on green')
            sleep(1)
            LED.switch_on({LEDEnum.yellow})
            logging.debug('LED switch on yellow')
            sleep(1)
            LED.switch_on({LEDEnum.red})
            logging.debug('LED switch on red')
            sleep(2)
            LED.blink_on({LEDEnum.green})
            logging.debug('LED blink on green')
            sleep(1)
            LED.blink_on({LEDEnum.yellow})
            logging.debug('LED blink on yellow')
            sleep(1)
            LED.blink_on({LEDEnum.red})
            logging.debug('LED blink on red')
            sleep(1)
            LED.switch_on({})  # type: ignore
            ApiServer.flask_shutdown_blocked = False
            ApiServer.last_msg = 'led_test ended'
        else:
            ApiServer.last_msg = 'not in State START'
        return redirect(url_for('get_defaults'))

    @ staticmethod
    @ app.route('/test_display')
    def test_display():
        """ start simple display test """
        from scrabblewatch import ScrabbleWatch

        if State().current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            watch = ScrabbleWatch()
            watch.display.show_boot()
            logging.debug('Display show boot')
            sleep(0.5)
            watch.display.show_cam_err()
            logging.debug('Display show cam err')
            sleep(0.5)
            watch.display.show_ftp_err()
            logging.debug('Display show ftp err')
            sleep(0.5)
            watch.display.show_ready()
            logging.debug('Display show ready')
            sleep(0.5)
            ApiServer.flask_shutdown_blocked = False
            ApiServer.last_msg = 'display_test ended'
        else:
            ApiServer.last_msg = 'not in State START'
        return redirect(url_for('get_defaults'))

    @ staticmethod
    @ app.route('/status', methods=['POST', 'GET'])
    @ app.route('/game_status', methods=['POST', 'GET'])
    def game_status():
        """ get request to current game state """
        return State().game.json_str(), 201

    @ staticmethod
    @ app.route('/shutdown', methods=['POST', 'GET'])
    def shutdown():
        """ process reboot """
        ApiServer.last_msg = '**** System shutdown ****'
        config.config.set('system', 'quit', 'shutdown')  # set temporary shutdown
        State().do_reboot()
        alarm(2)
        return redirect(url_for('get_defaults'))

    @ staticmethod
    @ app.route('/reboot', methods=['POST', 'GET'])
    def do_reboot():
        """ process reboot """
        ApiServer.last_msg = '**** System reboot ****'
        config.config.set('system', 'quit', 'reboot')  # set temporary reboot
        State().do_reboot()
        alarm(2)
        return redirect(url_for('get_defaults'))

    @ staticmethod
    @ app.route('/end', methods=['POST', 'GET'])
    def do_end():
        """ end app """
        ApiServer.last_msg = '**** Exit application ****'
        config.config.set('system', 'quit', 'end')  # set temporary end app
        alarm(1)
        return redirect(url_for('get_defaults'))

    @ sock.route('/ws_status')
    def echo(sock):
        logging.debug('call /ws_status')
        state = State()
        while True:
            if state.op_event.is_set():
                state.op_event.clear()
            _, (clock1, clock2), _ = state.watch.status()
            clock1 = config.max_time - clock1
            clock2 = config.max_time - clock2
            json = state.game.json_str()
            logging.debug(f'send socket {state.current_state} clock1 {clock1} clock2: {clock2}')
            if (state.current_state in ['S0', 'S1', 'P0', 'P1']) and state.picture is not None:
                _, im_buf_arr = cv2.imencode(".jpg", state.picture)
                png_output = base64.b64encode(im_buf_arr)
                logging.debug('b64encode')
                sock.send(f'{{"op": "{state.current_state}", "clock1": {clock1},"clock2": {clock2}, '  # type: ignore
                          f'"image": "{png_output}", "status": {json}  }}')
            else:
                sock.send(f'{{"op": "{state.current_state}", "clock1": {clock1},"clock2": {clock2}, '  # type:ignore
                          f'"status": {json}  }}')
            state.op_event.wait()

    def start_server(self, host: str = '0.0.0.0', port=5050, simulator=False):
        """ start flask server """
        logging.info('start api server')
        # flask log only error
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        ApiServer.simulator = simulator
        version_info = subprocess.run(['git', 'describe', '--tags'], check=False,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if version_info.returncode > 0:
            version_info = subprocess.run(['git', 'rev-parse', 'HEAD'], check=False,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ApiServer.scrabscrap_version = version_info.stdout.decode()[:7]
        if os.path.exists(f'{config.src_dir}/static/webapp/index.html'):
            ApiServer.local_webapp = True
            try:
                wip: str = netifaces.ifaddresses('wlan0')[netifaces.AF_INET][0]['addr']
                with open(f'{config.web_dir}/websocket.js', 'w') as f:
                    f.write(f'var WS_URL="ws://{wip}:{port}/ws_status"')
            except Exception:
                logging.warning('wlan0 not found')
        self.app.config['DEBUG'] = False
        self.app.config['TESTING'] = False
        self.server = make_server(host=host, port=port, threaded=True, app=self.app)  # pylint: disable=W0201
        self.ctx = self.app.app_context()   # pylint: disable=W0201
        self.ctx.push()
        self.server.serve_forever()

    def stop_server(self):
        """ stop flask server """
        logging.warning(f'server shutdown blocked: {ApiServer.flask_shutdown_blocked} ... waiting')
        while ApiServer.flask_shutdown_blocked:
            sleep(0.1)
        self.server.shutdown()


def main():
    """ main for standalone test """
    # for testing
    from threading import Event

    from hardware.camera_thread import Camera

    logging.config.fileConfig(fname=f'{config.work_dir}/log.conf',
                              disable_existing_loggers=False,
                              defaults={'level': 'DEBUG',
                                        'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})

    cam = Camera()
    _ = pool.submit(cam.update, Event())

    api = ApiServer(cam=cam)
    pool.submit(api.start_server)

    sleep(240)  # stop after 2 min
    api.stop_server()
    cam.cancel()


if __name__ == '__main__':
    main()
