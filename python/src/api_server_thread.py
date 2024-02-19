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
from time import perf_counter, sleep

import cv2
import numpy as np
from flask import (Flask, abort, redirect, render_template, request, send_file,
                   send_from_directory, url_for)
from flask_sock import ConnectionClosed, Sock
from werkzeug.serving import make_server

import upload
from config import config
from display import DisplayMock
from game_board.board import overlay_grid
from hardware import camera
from processing import get_last_warp, warp_image
from scrabblewatch import ScrabbleWatch
from state import EOG, START, State
from threadpool import pool
from upload_impl import upload_config


class ApiServer:  # pylint: disable=too-many-public-methods
    """ definition of flask server """
    app = Flask(__name__)
    sock = Sock(app)
    last_msg = ''
    prev_msg = ''
    flask_shutdown_blocked = False
    scrabscrap_version = ''
    simulator = False
    tailscale = False
    local_webapp = False

    @staticmethod
    def _clear_message():
        if ApiServer.last_msg != '' and ApiServer.prev_msg == ApiServer.last_msg:
            ApiServer.last_msg = ''
        ApiServer.prev_msg = ApiServer.last_msg

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
        ApiServer._clear_message()
        if request.method == 'POST':
            if request.form.get('btnplayer'):
                if (player1 := request.form.get('player1')) and (player2 := request.form.get('player2')) and \
                        (player1.casefold() != player2.casefold()):
                    ApiServer.last_msg = f'set player1={player1} / player2={player2}'
                    State.do_new_player_names(player1, player2)
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
        (player1, player2) = State.game.nicknames
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
        img = camera.cam.read()
        if img is not None:
            _, im_buf_arr = cv2.imencode(".jpg", img)
            png_output = base64.b64encode(bytes(im_buf_arr))
            warped, _ = warp_image(img)
            warp_coord = json.dumps(get_last_warp().tolist())  # type: ignore
            overlay = overlay_grid(warped)
            _, im_buf_arr = cv2.imencode(".jpg", overlay)
            png_overlay = base64.b64encode(bytes(im_buf_arr))
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
                    logging.info(f'development.recording changed to {recording}')
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
        def get_coord(_coord) -> str:
            (_col, _row) = _coord
            return chr(ord('A') + _row) + str(_col + 1)

        ApiServer._clear_message()
        game = State.game
        if request.method == 'POST':  # pylint: disable=too-many-nested-blocks
            if request.form.get('btnplayer'):
                if (player1 := request.form.get('player1')) and (player2 := request.form.get('player2')) and \
                        (player1.casefold() != player2.casefold()):
                    ApiServer.last_msg = f'set player1={player1} / player2={player2}'
                    State.do_new_player_names(player1, player2)
                else:
                    ApiServer.last_msg = f'can not set: {request.form.get("player1")}/{request.form.get("player2")}'
            elif request.form.get('btnblanko'):
                if (coord := request.form.get('coord')) and (char := request.form.get('char')) and char.isalpha():
                    char = char.lower()
                    ApiServer.last_msg = f'set blanko: {coord} = {char}'
                    State.do_set_blankos(coord, char)
                else:
                    ApiServer.last_msg = 'invalid character for blanko'
            elif request.form.get('btnscore'):
                logging.debug('in btnscore')
                if (move_number := request.form.get('move.move', type=int)) is not None and \
                    (score0 := request.form.get('move.score0', type=int)) is not None and \
                        (score1 := request.form.get('move.score1', type=int)) is not None:
                    logging.info(f'in values {move_number}: new score {(score0, score1)}')
                    if 0 < move_number <= len(game.moves) and (game.moves[move_number - 1].score != (score0, score1)):
                        ApiServer.last_msg = f'update move# {move_number}: new score {(score0, score1)}'
                        State.do_change_score(move_number, (score0, score1))
                    else:
                        ApiServer.last_msg = f'invalid move {move_number} or no changes in score {(score0, score1)}'
            elif request.form.get('btninsmoves'):
                logging.debug('in btninsmove')
                if (move_number := request.form.get('move.move', type=int)) is not None:
                    if 0 < move_number <= len(game.moves):
                        ApiServer.last_msg = f'insert two exchanges before move# {move_number}'
                        State.do_insert_moves(move_number)
                    else:
                        ApiServer.last_msg = f'invalid move {move_number}'
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
                        State.do_edit_move(int(move_number), (0, 0), True, '')
                    else:
                        vert, col, row = move.calc_coord(coord)  # type: ignore
                        if (str(move.type.name) != move_type) or (move.coord != (col, row)) or (move.word != word) \
                                or (move.is_vertical != vert):
                            if re.compile('[A-Z_\\.]+').match(word):
                                ApiServer.last_msg = f'try to correct move #{move_number} to {coord} {word}'
                                State.do_edit_move(int(move_number), (col, row), vert, word)
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
    @ app.route('/end_game', methods=['POST', 'GET'])
    def do_end_game():
        """ end current game """
        State.do_end_of_game()
        ApiServer.last_msg = 'end game'
        return redirect('/index')

    @ staticmethod
    @ app.route('/new_game', methods=['POST', 'GET'])
    def do_new_game():
        """ start new game game """
        if State.current_state not in (EOG, START):
            State.do_end_of_game()
        State.do_new_game()
        ApiServer.last_msg = 'start new game'
        return redirect('/index')

    @ staticmethod
    @ app.route('/settings', methods=['GET', 'POST'])
    def route_settings():
        """display settings on web page"""
        ApiServer._clear_message()
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
                    if option in ('upload_modus'):  # reload upload configuratio
                        upload.update_upload_mode()
                        upload_config.reload()
            except ValueError:
                logging.error(f'Error on settings: {request.form.items()}')
                ApiServer.last_msg = 'error: Value error in Parameter'
            return redirect('/settings')
        if request.method == 'POST' and request.form.get('btnupload'):
            password = request.form.get('password')
            if (server := request.form.get('server')) and (user := request.form.get('user')):
                upload_config.server = server
                upload_config.user = user
                if password is not None:
                    upload_config.password = password
                upload_config.store()
                ApiServer.last_msg = 'upload config saved'
        # fall through: request.method == 'GET':
        out = StringIO()
        config.config.write(out)
        return render_template('settings.html', apiserver=ApiServer, settingsinfo=out.getvalue(),
                               server=upload_config.server, user=upload_config.user)

    @ staticmethod
    @ app.route('/wifi', methods=['GET', 'POST'])
    def route_wifi():
        """ set wifi param (ssid, psk) via post request """
        ApiServer._clear_message()
        if request.method == 'POST':
            if request.form.get('btnadd'):
                if (ssid := request.form.get('ssid')) and (key := request.form.get('psk')):
                    process = subprocess.call(
                        f"sudo -n sh -c 'wpa_passphrase {ssid} {key} | sed \"/^.*ssid=.*/i priority=10\""
                        " >> /etc/wpa_supplicant/wpa_supplicant-wlan0.conf'", shell=True)
                    process1 = subprocess.call(
                        "sudo -n /usr/sbin/wpa_cli reconfigure -i wlan0", shell=True)
                    ApiServer.last_msg = f'configure wifi return={process}; reconfigure wpa return={process1}'
                    logging.info(f'{ApiServer.last_msg}')
                    sleep(5)
                    State.do_new_game()
            elif request.form.get('btnselect'):
                process = -1
                for i in request.form.keys():
                    logging.info(f'wpa network select {i}')
                    process = subprocess.call(f"sudo -n /usr/sbin/wpa_cli select_network {i} -i wlan0", shell=True)
                sleep(5)
                ApiServer.last_msg = f'select wifi return={process}'
                logging.info(f'{ApiServer.last_msg}')
                State.do_new_game()
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
                        logging.info(f'wpa network delete {i}')
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
        State.do_reboot()
        alarm(2)
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/shutdown', methods=['POST', 'GET'])
    def do_shutdown():
        """ process reboot """
        ApiServer.last_msg = '**** System shutdown ****'
        config.config.set('system', 'quit', 'shutdown')  # set temporary shutdown
        State.do_reboot()
        alarm(2)
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/test_display')
    def do_test_display():
        """ start simple display test """

        if State.current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            logging.debug('run display test')
            ScrabbleWatch.display.show_boot()
            sleep(0.5)
            ScrabbleWatch.display.show_cam_err()
            sleep(0.5)
            ScrabbleWatch.display.show_ftp_err()
            sleep(0.5)
            ScrabbleWatch.display.show_ready()
            sleep(0.5)
            ApiServer.flask_shutdown_blocked = False
            ApiServer.last_msg = 'display_test ended'
        else:
            ApiServer.last_msg = 'not in State START'
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/test_analyze')
    def do_test_analyze():  # pylint: disable=too-many-locals
        """ start simple analyze test """
        from concurrent import futures

        from processing import analyze, filter_image  # , filter_candidates
        from scrabble import board_to_string

        def _chunkify(lst, chunks):
            return [lst[i::chunks] for i in range(chunks)]

        if State.current_state in ('START', 'EOG', 'P0', 'P1'):
            log_message = 'run analyze test'

            ApiServer.flask_shutdown_blocked = True
            logging.info(log_message)

            img = camera.cam.read(peek=True)

            start = perf_counter()
            warped, warped_gray = warp_image(img)
            _, tiles_candidates = filter_image(warped)
            # tiles_candidates = filter_candidates((7, 7), tiles_candidates, set())
            board = {}
            chunks = _chunkify(list(tiles_candidates), 3)                           # 5. picture analysis
            future1 = pool.submit(analyze, warped_gray, board, set(chunks[0]))           # 1. thread
            future2 = pool.submit(analyze, warped_gray, board, set(chunks[1]))           # 2. thread
            analyze(warped_gray, board, set(chunks[2]))                                  # 3. (this) thread
            futures.wait({future1, future2})                                        # 6. blocking wait
            logging.info(f'analyze took {(perf_counter()-start):.4f} sec(s).')

            logging.info(f'\n{board_to_string(board)}')
            # find log
            process = subprocess.run(['tail', '-200', f'{config.log_dir}/messages.log'], check=False,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log_out = process.stdout.decode()
            if (f := log_out.rfind(log_message)) > 0:
                log_out = log_out[f + len(log_message):]
            # create b64 image
            _, im_buf_arr = cv2.imencode(".jpg", overlay_grid(warped))
            png_overlay = base64.b64encode(bytes(im_buf_arr))

            ApiServer.flask_shutdown_blocked = False
            ApiServer.last_msg = log_out
            return render_template('analyze.html', apiserver=ApiServer, log=log_out, img_data=urllib.parse.quote(png_overlay))
        ApiServer.last_msg = 'not in State START, EOG, P0, P1'
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/test_upload')
    def do_test_upload():
        """ is ftp accessible  """

        ApiServer.last_msg = 'test upload config entries\n'
        if upload_config.server is None:
            ApiServer.last_msg += "no server entry found\n"
        if upload_config.user in (None, ''):
            ApiServer.last_msg += "no user entry found\n"
        if upload_config.password in (None, ''):
            ApiServer.last_msg += "no password entry found\n"

        try:
            result = upload.upload.upload_status()
            ApiServer.last_msg += 'upload success' if result else 'upload = False'
        except IOError as oops:
            logging.error(f'http: I/O error({oops.errno}): {oops.strerror}')
            ApiServer.last_msg += f'http: I/O error({oops.errno}): {oops.strerror}'
        return redirect(url_for('route_index'))

    @ staticmethod
    @ app.route('/test_led')
    def do_test_led():
        """ start simple led test """
        from hardware.led import LED, LEDEnum

        if State.current_state == 'START':
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
    @ app.route('/vpn', defaults={'op': 'status'})
    @ app.route('/vpn/<path:op>')
    def do_vpn(op):
        """install vpn ops (start, stop, status, install, auth, uninstall)
        """
        if op == 'status':
            os.system(f'{config.src_dir}/../../scripts/tailscale.sh STATUS | tee -a {config.log_dir}/messages.log &')
        elif op == 'install':
            os.system(f'{config.src_dir}/../../scripts/tailscale.sh INSTALL | tee -a {config.log_dir}/messages.log &')
        elif op == 'start':
            os.system(f'{config.src_dir}/../../scripts/tailscale.sh UP | tee -a {config.log_dir}/messages.log &')
        elif op == 'stop':
            os.system(f'{config.src_dir}/../../scripts/tailscale.sh DOWN | tee -a {config.log_dir}/messages.log &')
        elif op == 'auth':
            os.system(f'{config.src_dir}/../../scripts/tailscale.sh REAUTH | tee -a {config.log_dir}/messages.log &')
        elif op == 'uninstall':
            os.system(f'{config.src_dir}/../../scripts/tailscale.sh UNINSTALL | tee -a {config.log_dir}/messages.log &')
        else:
            logging.warning('invalid operation for vpn')
        ApiServer.tailscale = os.path.isfile('/usr/bin/tailscale')
        return redirect(url_for('route_logs'))

    @ staticmethod
    @ app.route('/upgrade_scrabscrap')
    def do_update_scrabscrap():
        """ start scrabscrap upgrade """

        if State.current_state == 'START':
            ScrabbleWatch.display.show_ready(('Update...', 'pls wait'))
            os.system(f'{config.src_dir}/../../scripts/upgrade.sh {config.system_gitbranch} |'
                      f' tee -a {config.log_dir}/messages.log &')
            return redirect(url_for('route_logs'))
        ApiServer.last_msg = 'not in State START'
        return redirect(url_for('route_index'))

    @ sock.route('/ws_log')
    def ws_log(sock):  # pylint: disable=no-self-argument
        """websocket for logging"""
        f = open(f'{config.log_dir}/messages.log', 'r', encoding='utf-8')  # pylint: disable=consider-using-with
        # with will close at eof
        tmp = '\n' + ''.join(f.readlines()[-200:])    # first read last 200 lines
        sock.send(tmp)  # type: ignore  # pylint: disable=no-member
        while True:
            tmp = f.readline()
            if tmp and tmp != '':   # new data available
                try:
                    sock.send(tmp)  # type: ignore  # pylint: disable=no-member
                except ConnectionClosed:
                    f.close()
                    return
            else:
                sleep(0.5)

    @ staticmethod
    @ app.route('/status', methods=['POST', 'GET'])
    @ app.route('/game_status', methods=['POST', 'GET'])
    def game_status():
        """ get request to current game state """
        return State.game.json_str(), 201

    @ sock.route('/ws_status')
    def echo(sock):  # pylint: disable=no-self-argument
        """websocket endpoint"""
        logging.debug('call /ws_status')
        while True:
            if State.op_event.is_set():
                State.op_event.clear()
            _, (clock1, clock2), _ = ScrabbleWatch.status()
            clock1 = config.max_time - clock1
            clock2 = config.max_time - clock2
            jsonstr = State.game.json_str()
            logging.debug(f'send socket {State.current_state} clock1 {clock1} clock2: {clock2}')
            try:
                if (State.current_state in ['S0', 'S1', 'P0', 'P1']) and State.picture is not None:
                    _, im_buf_arr = cv2.imencode(".jpg", State.picture)
                    png_output = base64.b64encode(bytes(im_buf_arr))
                    logging.debug('b64encode')
                    sock.send(f'{{"op": "{State.current_state}", '  # type: ignore  # pylint: disable=no-member
                              f'"clock1": {clock1},"clock2": {clock2}, "image": "{png_output}", "status": {jsonstr}  }}')
                else:
                    sock.send(f'{{"op": "{State.current_state}", '  # type:ignore  # pylint: disable=no-member
                              f'"clock1": {clock1},"clock2": {clock2}, "status": {jsonstr}  }}')
            except ConnectionClosed:
                return
            State.op_event.wait()

    def start_server(self, host: str = '0.0.0.0', port=5050, simulator=False):
        """ start flask server """
        logging.info('start api server')
        # flask log only error
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        ApiServer.simulator = simulator
        ApiServer.tailscale = os.path.isfile('/usr/bin/tailscale')
        version_dirty = subprocess.run(['git', 'diff', '--stat'], check=False,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        version_flag: str = '\u2757' if len(version_dirty.stdout) > 0 else ''
        version_info = subprocess.run(['git', 'describe', '--tags'], check=False,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if version_info.returncode > 0:
            version_info = subprocess.run(['git', 'rev-parse', 'HEAD'], check=False,
                                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        branch_info = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], check=False,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        branch = '' if 'main' == branch_info.stdout.decode().strip() else f'({branch_info.stdout.decode().strip()})'
        ApiServer.scrabscrap_version = f'{branch} {version_flag}{version_info.stdout.decode()[:14]}'
        logging.info(f'ScrabScrap Version: {ApiServer.scrabscrap_version}')
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
            sleep(0.01)
        self.server.shutdown()


def main():
    """ main for standalone test """
    # for testing
    from threading import Event

    from hardware.camera import switch_camera

    logging.config.fileConfig(fname=f'{config.work_dir}/log.conf',
                              disable_existing_loggers=False,
                              defaults={'level': 'DEBUG',
                                        'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'})

    # set Mock-Display
    ScrabbleWatch.display = DisplayMock()

    # set Mock-Camera
    switch_camera('file')

    _ = pool.submit(camera.cam.update, Event())

    api = ApiServer()
    pool.submit(api.start_server)

    sleep(240)  # stop after 2 min
    api.stop_server()
    camera.cam.cancel()


if __name__ == '__main__':
    main()
