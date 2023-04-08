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
import numpy as np
from flask import (Flask, abort, redirect, render_template, request, send_file,
                   send_from_directory, url_for)
from flask_sock import Sock
from werkzeug.serving import make_server

from config import config
from game_board.board import overlay_grid
from processing import (admin_change_move, admin_change_score, get_last_warp,
                        set_blankos, warp_image)
from state import State
from threadpool import pool
from upload_config import UploadConfig


class ApiServer:  # pylint: disable=too-many-public-methods
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
    @app.route('/', methods=['GET', 'POST'])
    @app.route('/index', methods=['GET', 'POST'])
    def route_index():
        """ index web page """
        state = State()
        if request.method == 'POST':
            if request.form.get('btnplayer'):
                if (player1 := request.form.get('player1')) and (player2 := request.form.get('player2')) and \
                        (player1.casefold() != player2.casefold()):
                    ApiServer.last_msg = f'set player1={player1} / player2={player2}'
                    state.do_new_player_names(player1, player2)
                else:
                    ApiServer.last_msg = f'can not set: {request.form.get("player1")}/{request.form.get("player2")}'
            elif request.form.get('btntournament'):
                if (tournament := request.form.get('tournament')) is not None and (tournament != config.tournament):
                    if 'scrabble' not in config.config.sections():
                        config.config.add_section('scrabble')
                    config.config.set('scrabble', 'tournament', str(tournament))
                    config.save()
                    ApiServer.last_msg = f'set tournament={tournament}'
                else:
                    ApiServer.last_msg = f'can not set: tournament={tournament}'
            return redirect('/index')
        (player1, player2) = state.game.nicknames
        tournament = config.tournament
        # fall through: request.method == 'GET':
        return render_template('index.html', apiserver=ApiServer, player1=player1, player2=player2, tournament=tournament)

    @ staticmethod
    @ app.route('/cam', methods=['GET', 'POST'])
    def route_cam():
        """ display current camera picture """
        if request.method == 'POST':
            if request.form.get('btndelete'):
                config.config.remove_option('video', 'warp_coordinates')
                config.save()
            elif request.form.get('btnstore'):
                if 'video' not in config.config.sections():
                    config.config.add_section('video')
                config.config.set('video', 'warp_coordinates', request.form.get('warp_coordinates'))
                config.save()
            return redirect('/cam')
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
    @ app.route('/loglevel', methods=['GET', 'POST'])
    def route_loglevel():
        """ settings loglevel, recording """
        if request.method == 'POST':
            try:
                if (new_level := request.form.get('loglevel', type=int)) is not None:
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
                return redirect('/index')
            return redirect('/loglevel')
        # fall through: request.method == 'GET':
        loglevel = logging.getLogger('root').getEffectiveLevel()
        return render_template('loglevel.html', apiserver=ApiServer, recording=f'{config.development_recording}',
                               loglevel=f'{loglevel}')

    @ staticmethod
    @ app.route('/logs')
    def route_logs():
        """ display message log """
        log_out = '## loading log ##'
        return render_template('logs.html', apiserver=ApiServer, log=log_out)

    @staticmethod
    @app.route('/moves', methods=['GET', 'POST'])
    def route_moves():  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """ edit moves form """
        def get_coord(coord) -> str:
            (col, row) = coord
            return chr(ord('A') + row) + str(col + 1)

        state = State()
        game = state.game
        if request.method == 'POST':  # pylint: disable=too-many-nested-blocks
            if request.form.get('btnplayer'):
                if (player1 := request.form.get('player1')) and (player2 := request.form.get('player2')) and \
                        (player1.casefold() != player2.casefold()):
                    ApiServer.last_msg = f'set player1={player1} / player2={player2}'
                    State().do_new_player_names(player1, player2)
                else:
                    ApiServer.last_msg = f'can not set: {request.form.get("player1")}/{request.form.get("player2")}'
            elif request.form.get('btnblanko'):
                if (coord := request.form.get('coord')) and (char := request.form.get('char')) and char.isalpha():
                    char = char.lower()
                    ApiServer.last_msg = f'set blanko: {coord} = {char}'
                    set_blankos(game, coord, char, event=state.op_event)
                else:
                    ApiServer.last_msg = 'invalid character for blanko'
            elif request.form.get('btnscore'):
                logging.debug('in btnscore')
                if (move_number := request.form.get('move.move', type=int)) is not None and \
                    (score0 := request.form.get('move.score0', type=int)) is not None and \
                        (score1 := request.form.get('move.score1', type=int)) is not None:
                    logging.debug(f'in values {move_number}: new score {(score0, score1)}')
                    if 0 < move_number <= len(game.moves) and (game.moves[move_number - 1].score != (score0, score1)):
                        logging.debug('in set')
                        ApiServer.last_msg = f'update move# {move_number}: new score {(score0, score1)}'
                        admin_change_score(game, move_number, (score0, score1), state.op_event)
                    else:
                        ApiServer.last_msg = f'invalid move {move_number} or no changes in score {(score0, score1)}'
            elif request.form.get('btnmove'):
                move_number = request.form.get('move.move', type=int) or 0
                move_type = request.form.get('move.type')
                coord = request.form.get('move.coord')
                word = request.form.get('move.word')
                word = word.upper().replace(' ', '_') if word else ''
                if 0 < move_number <= len(game.moves):
                    move = game.moves[move_number - 1]
                    if (move_type == 'EXCHANGE') and (move.type.name != move_type):
                        ApiServer.last_msg = f'try to correct move #{move_number} to exchange'
                        admin_change_move(game, int(move_number), (0, 0), True, '', state.op_event)
                    else:
                        vert, col, row = move.calc_coord(coord)  # type: ignore
                        if (str(move.type.name) != move_type) or (move.coord != (col, row)) or (move.word != word) \
                                or (move.is_vertical != vert):
                            if re.compile('[A-Z_\\.]+').match(word):
                                ApiServer.last_msg = f'try to correct move #{move_number} to {coord} {word}'
                                admin_change_move(game, int(move_number), (col, row), vert, word, state.op_event)
                            else:
                                ApiServer.last_msg = f'invalid character in word {word}'
                        else:
                            ApiServer.last_msg = ' no changes detected'
            return redirect('/moves')
        # fall through: request.method == 'GET':
        (player1, player2) = game.nicknames
        blankos = [(get_coord(key), val) for key, (val, _) in game.moves[-1].board.items()
                   if val.islower() or val == '_'] if game.moves else []
        return render_template('moves.html', apiserver=ApiServer, player1=player1, player2=player2,
                               move_list=game.moves, blanko_list=blankos)

    @ staticmethod
    @ app.route('/settings', methods=['GET', 'POST'])
    def route_settings():
        """display settings on web page"""
        if request.method == 'POST' and request.form.get('btnset'):
            try:
                if (path := request.form.get('setting')):
                    value = request.form.get('value')
                    section, option = str(path).split('.', maxsplit=2)
                    if value is not None and value != '':
                        if value.lower() == 'true':
                            value = 'True'
                        if value.lower() == 'false':
                            value = 'False'
                        if section not in config.config.sections():
                            config.config.add_section(section)
                        config.config.set(section, option, str(value))
                        ApiServer.last_msg = f'set option {section}.{option}={value}'
                    else:
                        config.config.remove_option(section, option)
                        ApiServer.last_msg = f'delete {section}.{option}'
                    config.save()
            except ValueError:
                logging.error(f'Error on settings: {request.form.items()}')
                ApiServer.last_msg = 'error: Value error in Parameter'
            return redirect('/settings')
        if request.method == 'POST' and request.form.get('btnupload'):
            password = request.form.get('password')
            if (server := request.form.get('server')) and (user := request.form.get('user')):
                UploadConfig().server = server
                UploadConfig().user = user
                if password is not None:
                    UploadConfig().password = password
                UploadConfig().store()
                ApiServer.last_msg = 'upload config saved'
        # fall through: request.method == 'GET':
        out = StringIO()
        config.config.write(out)
        return render_template('settings.html', apiserver=ApiServer, settingsinfo=out.getvalue(),
                               server=UploadConfig().server, user=UploadConfig().user)

    @ staticmethod
    @ app.route('/wifi', methods=['GET', 'POST'])
    def route_wifi():
        """ set wifi param (ssid, psk) via post request """
        if request.method == 'POST':
            state = State()
            if request.form.get('btnadd'):
                if (ssid := request.form.get('ssid')) and (key := request.form.get('psk')):
                    process = subprocess.call(
                        f"sudo -n sh -c 'wpa_passphrase {ssid} {key} | sed \"/^.*ssid=.*/i priority=10\""
                        " >> /etc/wpa_supplicant/wpa_supplicant-wlan0.conf'", shell=True)
                    process1 = subprocess.call(
                        "sudo -n /usr/sbin/wpa_cli reconfigure -i wlan0", shell=True)
                    ApiServer.last_msg = f'configure wifi return={process}; reconfigure wpa return={process1}'
                    sleep(5)
                    state.do_new_game()
            elif request.form.get('btnselect'):
                for i in request.form.keys():
                    logging.debug(f'wpa network select {i}')
                    _ = subprocess.call(f"sudo -n /usr/sbin/wpa_cli select_network {i} -i wlan0", shell=True)
                sleep(5)
                state.do_new_game()
            elif request.form.get('btnscan'):
                _ = subprocess.run(['sudo', '-n', '/usr/sbin/wpa_cli', 'scan', '-i', 'wlan0'], check=False,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                sleep(3)
                process2 = subprocess.run(['sudo', '-n', '/usr/sbin/wpa_cli', 'scan_results', '-i', 'wlan0'], check=False,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                ApiServer.last_msg = f'{process2.stdout.decode()}'
            elif request.form.get('btndelete'):
                for i in request.form.keys():
                    if request.form.get(i) == 'on':
                        logging.debug(f'wpa network delete {i}')
                        _ = subprocess.call(f"sudo -n /usr/sbin/wpa_cli remove_network {i} -i wlan0", shell=True)
                    _ = subprocess.call("sudo -n /usr/sbin/wpa_cli save_config -i wlan0", shell=True)
            return redirect('/wifi')
        # fall through: request.method == 'GET':
        process1 = subprocess.run(['sudo', '-n', '/usr/sbin/wpa_cli', 'list_networks', '-i', 'wlan0'], check=False,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        wifi_raw = process1.stdout.decode().split(sep='\n')[1:-1]
        wifi_list = [element.split(sep='\t') for element in wifi_raw]
        return render_template('wifi.html', apiserver=ApiServer, wifi_list=wifi_list)

    @ staticmethod
    @ app.route('/delete_logs', methods=['POST', 'GET'])
    def do_delete_logs():
        """ delete message logs """
        import glob
        ignore_list = [f'{config.log_dir}/messages.log', f'{config.log_dir}/game.log']
        file_list = glob.glob(f'{config.log_dir}/*')
        file_list = [f for f in file_list if f not in ignore_list]
        # Iterate over the list of filepaths & remove each file.
        ApiServer.last_msg = 'delete logs'
        for file_path in file_list:
            try:
                os.remove(file_path)
            except OSError:
                ApiServer.last_msg += f'\nerror: {file_path}'
        for filename in ignore_list:
            with open(filename, 'w', encoding='UTF-8'):
                pass  # empty log file
        return redirect('/index')

    @ staticmethod
    @ app.route('/delete_recording', methods=['POST', 'GET'])
    def do_delete_recording():
        """ delete recording(s) """
        import glob
        logging.debug(f'path {config.work_dir}/recording')
        ignore_list = [f'{config.work_dir}/recording/gameRecording.log']
        file_list = glob.glob(f'{config.work_dir}/recording/*')
        file_list = [f for f in file_list if f not in ignore_list]
        # Iterate over the list of filepaths & remove each file.
        ApiServer.last_msg = 'delete recording'
        for file_path in file_list:
            try:
                os.remove(file_path)
            except OSError:
                ApiServer.last_msg += f'\nerror: {file_path}'
        with open(f'{config.work_dir}/recording/gameRecording.log', 'w', encoding='UTF-8'):
            pass  # empty log file
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/download_games', defaults={'req_path': ''})
    @ app.route('/download_games/<path:req_path>')
    def do_download_games(req_path):
        """download files from web folder"""
        base_path = config.web_dir
        fullpath = os.path.normpath(os.path.join(base_path, req_path))
        # validate path
        if not fullpath.startswith(base_path):
            return abort(404)
        # Return 404 if path doesn't exist
        if not os.path.exists(fullpath):
            return abort(404)
        # Check if path is a file and serve
        if os.path.isfile(fullpath):
            return send_file(fullpath)
        # read files
        file_objs = [x.name for x in os.scandir(fullpath)]
        file_objs.sort()
        return render_template('download_games.html', files=file_objs, apiserver=ApiServer,)

    @ staticmethod
    @ app.route('/download_logs', methods=['POST', 'GET'])
    def do_download_logs():
        """ download message logs """
        from zipfile import ZipFile

        with ZipFile(f'{config.log_dir}/log.zip', 'w') as _zip:
            files = ['game.log', 'messages.log']
            for filename in files:
                if os.path.exists(f'{config.log_dir}/{filename}'):
                    _zip.write(f'{config.log_dir}/{filename}')
        ApiServer.last_msg = ''
        return send_from_directory(f'{config.log_dir}', 'log.zip', as_attachment=True)

    @ staticmethod
    @ app.route('/download_recording', methods=['POST', 'GET'])
    def do_download_recording():
        """ download recordings """
        import glob
        from zipfile import ZipFile

        with ZipFile(f'{config.work_dir}/recording/recording.zip', 'w') as _zip:
            ignore_list = [f'{config.work_dir}/recording/recording.zip']
            file_list = glob.glob(f'{config.work_dir}/recording/*')
            file_list = [f for f in file_list if f not in ignore_list]
            for filename in file_list:
                _zip.write(f'{filename}')
        ApiServer.last_msg = ''
        return send_from_directory(f'{config.work_dir}/recording', 'recording.zip', as_attachment=True)

    @ staticmethod
    @ app.route('/end', methods=['POST', 'GET'])
    def do_end():
        """ end app """
        ApiServer.last_msg = '**** Exit application ****'
        config.config.set('system', 'quit', 'end')  # set temporary end app
        alarm(1)
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/reboot', methods=['POST', 'GET'])
    def do_reboot():
        """ process reboot """
        ApiServer.last_msg = '**** System reboot ****'
        config.config.set('system', 'quit', 'reboot')  # set temporary reboot
        State().do_reboot()
        alarm(2)
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/shutdown', methods=['POST', 'GET'])
    def do_shutdown():
        """ process reboot """
        ApiServer.last_msg = '**** System shutdown ****'
        config.config.set('system', 'quit', 'shutdown')  # set temporary shutdown
        State().do_reboot()
        alarm(2)
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/test_display')
    def do_test_display():
        """ start simple display test """
        from scrabblewatch import ScrabbleWatch

        if State().current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            logging.debug('run display test')
            watch = ScrabbleWatch()
            watch.display.show_boot()
            sleep(0.5)
            watch.display.show_cam_err()
            sleep(0.5)
            watch.display.show_ftp_err()
            sleep(0.5)
            watch.display.show_ready()
            sleep(0.5)
            ApiServer.flask_shutdown_blocked = False
            ApiServer.last_msg = 'display_test ended'
        else:
            ApiServer.last_msg = 'not in State START'
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/test_ftp')
    def do_test_ftp():
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
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/test_led')
    def do_test_led():
        """ start simple led test """
        from hardware.led import LED, LEDEnum

        if State().current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            logging.debug('run LED test')
            LED.switch_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
            sleep(1)
            LED.blink_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
            sleep(2)
            LED.switch_on({LEDEnum.green})
            sleep(1)
            LED.switch_on({LEDEnum.yellow})
            sleep(1)
            LED.switch_on({LEDEnum.red})
            sleep(2)
            LED.blink_on({LEDEnum.green})
            sleep(1)
            LED.blink_on({LEDEnum.yellow})
            sleep(1)
            LED.blink_on({LEDEnum.red})
            sleep(1)
            LED.switch_on({})  # type: ignore
            ApiServer.flask_shutdown_blocked = False
            ApiServer.last_msg = 'led_test ended'
        else:
            ApiServer.last_msg = 'not in State START'
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/upgrade_scrabscrap')
    def do_update_scrabscrap():
        """ start scrabscrap upgrade """
        from scrabblewatch import ScrabbleWatch

        if State().current_state == 'START':
            watch = ScrabbleWatch()
            watch.display.show_ready(('Update...', 'pls wait'))
            os.system(f'{config.src_dir}/../../scripts/upgrade.sh {config.system_gitbranch} |'
                      f' tee -a {config.log_dir}/messages.log &')
            return redirect(url_for('route_logs'))
        ApiServer.last_msg = 'not in State START'
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/logentry')
    def logentry():
        """ returns last 100 log lines """
        process = subprocess.run(['tail', '-100', f'{config.log_dir}/messages.log'], check=False,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log_out = process.stdout.decode()
        return log_out

    @ staticmethod
    @ app.route('/status', methods=['POST', 'GET'])
    @ app.route('/game_status', methods=['POST', 'GET'])
    def game_status():
        """ get request to current game state """
        return State().game.json_str(), 201

    @ sock.route('/ws_status')
    def echo(sock):  # pylint: disable=no-self-argument
        """websocket endpoint"""
        logging.debug('call /ws_status')
        state = State()
        while True:
            if state.op_event.is_set():
                state.op_event.clear()
            _, (clock1, clock2), _ = state.watch.status()
            clock1 = config.max_time - clock1
            clock2 = config.max_time - clock2
            jsonstr = state.game.json_str()
            logging.debug(f'send socket {state.current_state} clock1 {clock1} clock2: {clock2}')
            if (state.current_state in ['S0', 'S1', 'P0', 'P1']) and state.picture is not None:
                _, im_buf_arr = cv2.imencode(".jpg", state.picture)
                png_output = base64.b64encode(im_buf_arr)
                logging.debug('b64encode')
                sock.send(f'{{"op": "{state.current_state}", '  # type: ignore  # pylint: disable=no-member
                          f'"clock1": {clock1},"clock2": {clock2}, "image": "{png_output}", "status": {jsonstr}  }}')
            else:
                sock.send(f'{{"op": "{state.current_state}", '  # type:ignore  # pylint: disable=no-member
                          f'"clock1": {clock1},"clock2": {clock2}, "status": {jsonstr}  }}')
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
        ApiServer.scrabscrap_version = version_info.stdout.decode()[:14]
        if os.path.exists(f'{config.src_dir}/static/webapp/index.html'):
            ApiServer.local_webapp = True
        self.app.config['DEBUG'] = False
        self.app.config['TESTING'] = False
        self.server = make_server(host=host, port=port, threaded=True,  # pylint: disable=attribute-defined-outside-init
                                  app=self.app)
        self.ctx = self.app.app_context()   # pylint: disable=attribute-defined-outside-init
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
