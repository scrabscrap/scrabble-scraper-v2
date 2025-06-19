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

# pylint: disable=too-many-lines
from __future__ import annotations

import base64
import binascii
import configparser
import hashlib
import json
import logging
import logging.config
import os
import platform
import re
import subprocess
import urllib.parse
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from signal import alarm
from time import perf_counter, sleep

import cv2
import numpy as np
import psutil
from flask import Flask, abort, redirect, render_template, request, send_file, send_from_directory, url_for
from flask_sock import ConnectionClosed, Sock
from werkzeug.serving import make_server

import upload
from config import config, version  # type: ignore # pylance error
from customboard import get_last_warp
from display import Display
from game_board.board import overlay_grid
from hardware import camera
from processing import (
    admin_change_move,
    admin_del_challenge,
    admin_ins_challenge,
    admin_insert_moves,
    admin_toggle_challenge_type,
    event_set,
    remove_blanko,
    set_blankos,
    warp_image,
)
from scrabble import MoveType
from scrabblewatch import ScrabbleWatch
from state import GameState, State
from threadpool import Command, command_queue, pool

logger = logging.getLogger(__name__)


class ApiServer:  # pylint: disable=too-many-public-methods
    """definition of flask server"""

    app = Flask(__name__)
    sock = Sock(app)
    last_msg = ''
    prev_msg = ''
    flask_shutdown_blocked = False
    scrabscrap_version = ''
    simulator = False
    tailscale = False
    local_webapp = False
    machine = platform.machine()

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
        """index web page"""
        ApiServer._clear_message()
        if request.method == 'POST':
            if request.form.get('btnplayer'):
                if (
                    (player1 := request.form.get('player1'))
                    and (player2 := request.form.get('player2'))
                    and (player1.casefold() != player2.casefold())
                ):
                    logger.info(f'set {player1=} / {player2=}')
                    State.ctx.game.set_player_names(player1, player2)
                    event_set(State.ctx.op_event)
                else:
                    logger.warning(f'can not set: {request.form.get("player1")}/{request.form.get("player2")}')
            elif request.form.get('btntournament'):
                if (tournament := request.form.get('tournament')) is not None and (tournament != config.scrabble.tournament):
                    if 'scrabble' not in config.config.sections():
                        config.config.add_section('scrabble')
                    config.config.set('scrabble', 'tournament', str(tournament))
                    config.save()
                    logger.info(f'set {tournament=}')
                else:
                    logger.warning(f'can not set: {tournament=}')
            return redirect('/index')
        (player1, player2) = State.ctx.game.nicknames
        tournament = config.scrabble.tournament
        # fall through: request.method == 'GET':
        return render_template('index.html', apiserver=ApiServer, player1=player1, player2=player2, tournament=tournament)

    @staticmethod
    @app.route('/cam', methods=['GET', 'POST'])
    def route_cam():  # pylint: disable=too-many-branches
        """display current camera picture"""
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
            logger.debug(f'coord x:{col} y:{row}')
            rect = get_last_warp()
            if rect is None:
                rect = np.array(
                    [[0, 0], [config.video.width, 0], [config.video.width, config.video.height], [0, config.video.height]],
                    dtype='float32',
                )
            if col < 200 and row < 200:
                rect[0] = (col, row)
            elif row < 200:
                rect[1] = (col, row)
            elif col < 200:
                rect[3] = (col, row)
            else:
                rect[2] = (col, row)
            logger.debug(f'new warp: {np.array2string(rect, formatter={"float_kind": lambda x: f"{x:.1f}"}, separator=", ")}')
            config.config.set(
                'video',
                'warp_coordinates',
                np.array2string(rect, formatter={'float_kind': lambda x: f'{x:.1f}'}, separator=','),
            )
        warp_coord_cnf = str(config.video.warp_coordinates)
        img = camera.cam.read()
        if img is not None:
            _, im_buf_arr = cv2.imencode('.jpg', img)
            png_output = base64.b64encode(bytes(im_buf_arr))
            warped, _ = warp_image(img)
            last_warped = get_last_warp()
            if last_warped is not None:
                warp_coord = json.dumps(last_warped.tolist())
            else:
                warp_coord = '[]'
            overlay = overlay_grid(warped)
            _, im_buf_arr = cv2.imencode('.jpg', overlay)
            png_overlay = base64.b64encode(bytes(im_buf_arr))
        else:
            png_output = ''
            png_overlay = ''
            warp_coord = ''
        return render_template(
            'cam.html',
            apiserver=ApiServer,
            img_data=urllib.parse.quote(png_output),
            warp_data=urllib.parse.quote(png_overlay),
            warp_coord=urllib.parse.quote(warp_coord),
            warp_coord_raw=warp_coord,
            warp_coord_cnf=warp_coord_cnf,
        )

    @staticmethod
    @app.route('/loglevel', methods=['GET', 'POST'])
    def route_loglevel():
        """settings loglevel, recording"""
        if request.method == 'POST':
            try:
                if (new_level := request.form.get('loglevel', type=int)) is not None:
                    root_logger = logging.getLogger('root')
                    prev_level = root_logger.getEffectiveLevel()
                    if new_level != prev_level:
                        logger.warning(f'loglevel changed to {logging.getLevelName(new_level)}')
                        root_logger.setLevel(new_level)
                        log_config = configparser.ConfigParser()
                        with (config.path.work_dir / 'log.conf').open(encoding='UTF-8') as config_file:
                            log_config.read_file(config_file)
                            if 'logger_root' not in log_config.sections():
                                log_config.add_section('logger_root')
                            log_config.set('logger_root', 'level', logging.getLevelName(new_level))
                        with (config.path.work_dir / 'log.conf').open('w', encoding='UTF-8') as config_file:
                            log_config.write(config_file)

                recording = 'recording' in request.form
                if config.development.recording != recording:
                    logger.info(f'development.recording changed to {recording}')
                    if 'development' not in config.config.sections():
                        config.config.add_section('development')
                    config.config.set('development', 'recording', str(recording))
                    config.save()
            except OSError as oops:
                logger.error(f'I/O error({oops.errno}): {oops.strerror}')
                return redirect('/index')
            return redirect('/loglevel')
        # fall through: request.method == 'GET':
        loglevel = logging.getLogger('root').getEffectiveLevel()
        return render_template(
            'loglevel.html', apiserver=ApiServer, recording=f'{config.development.recording}', loglevel=f'{loglevel}'
        )

    @staticmethod
    @app.route('/logs')
    def route_logs():
        """display message log"""
        return render_template('logs.html', apiserver=ApiServer)

    @staticmethod
    @app.route('/log_sysinfo', methods=['GET', 'POST'])
    def log_sysinfo():  # pylint: disable=too-many-locals,too-many-statements
        """log out system info"""

        def bytes2human(n):
            # http://code.activestate.com/recipes/578019
            # >>> bytes2human(10000)
            # '9.8K'
            # >>> bytes2human(100001221)
            # '95.4M'
            symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
            prefix = {}
            for i, s in enumerate(symbols):
                prefix[s] = 1 << (i + 1) * 10
            for s in reversed(symbols):
                if abs(n) >= prefix[s]:
                    value = float(n) / prefix[s]
                    return f'{value:.1f}{s}'
            return f'{n}B'

        logger.info(f'{"=" * 40} System Information {"=" * 40}')
        uname = platform.uname()
        logger.info(f'System: {uname.system}')
        logger.info(f'Node Name: {uname.node}')
        logger.info(f'Release: {uname.release}')
        logger.info(f'Version: {uname.version}')
        logger.info(f'Machine: {uname.machine}')
        logger.info(f'Processor: {uname.processor}')

        logger.info(f'{"=" * 40} Boot Time {"=" * 40}')
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.fromtimestamp(boot_time_timestamp)
        logger.info(f'Boot Time: {bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}')

        logger.info(f'{"=" * 40} CPU Info {"=" * 40}')
        logger.info(f'Physical cores: {psutil.cpu_count(logical=False)}')
        logger.info(f'Total cores: {psutil.cpu_count(logical=True)}')
        cpufreq = psutil.cpu_freq()
        logger.info(f'Max Frequency: {cpufreq.max:.2f}Mhz')
        logger.info(f'Min Frequency: {cpufreq.min:.2f}Mhz')
        logger.info(f'Current Frequency: {cpufreq.current:.2f}Mhz')
        logger.info('CPU Usage Per Core:')
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            logger.info(f'  Core {i}: {percentage}%')
        logger.info(f'Total CPU Usage: {psutil.cpu_percent()}%')
        load_avg_1, load_avg_5, load_avg_15 = psutil.getloadavg()
        logger.info(f'Load: {load_avg_1:.2f} {load_avg_5:.2f} {load_avg_15:.2f}')

        logger.info(f'{"=" * 40} Memory Information {"=" * 40}')
        svmem = psutil.virtual_memory()
        logger.info(f'Total: {bytes2human(svmem.total)}')
        logger.info(f'Available: {bytes2human(svmem.available)}')
        logger.info(f'Used: {bytes2human(svmem.used)}')
        logger.info(f'Percentage: {svmem.percent}%')

        logger.info(f'{"=" * 40} SWAP {"=" * 40}')
        swap = psutil.swap_memory()
        logger.info(f'Total: {bytes2human(swap.total)}')
        logger.info(f'Free: {bytes2human(swap.free)}')
        logger.info(f'Used: {bytes2human(swap.used)}')
        logger.info(f'Percentage: {swap.percent}%')

        logger.info(f'{"=" * 40} Disk Information {"=" * 40}')
        logger.info('Partitions and Usage:')
        partitions = psutil.disk_partitions()
        for partition in partitions:
            logger.info(f'=== Device: {partition.device} ===')
            logger.info(f'  Mountpoint: {partition.mountpoint}')
            logger.info(f'  File system type: {partition.fstype}')
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue
            logger.info(f'  Total Size: {bytes2human(partition_usage.total)}')
            logger.info(f'  Used: {bytes2human(partition_usage.used)}')
            logger.info(f'  Free: {bytes2human(partition_usage.free)}')
            logger.info(f'  Percentage: {partition_usage.percent}%')
        # get IO statistics since boot
        disk_io = psutil.disk_io_counters()
        if disk_io:
            logger.info(f'Total read: {bytes2human(disk_io.read_bytes)}')
            logger.info(f'Total write: {bytes2human(disk_io.write_bytes)}')

        logger.info(f'{"=" * 40} Process Info {"=" * 40}')
        for process in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            with suppress(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                if 'python' in process.info['name'].lower():
                    logger.info(
                        f'{process.info["pid"]:6} {process.info["name"]} '
                        f'mem:{process.info["memory_percent"]:.2f}% cpu:{process.info["cpu_percent"]:.2f}%'
                    )

        return redirect('/logs')

    @staticmethod
    @app.route('/moves', methods=['GET', 'POST'])
    def route_moves():  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """edit moves form"""

        def get_coord(_coord, is_vertical=False) -> str:
            (_col, _row) = _coord
            return str(_col + 1) + chr(ord('A') + _row) if is_vertical else chr(ord('A') + _row) + str(_col + 1)

        ApiServer._clear_message()
        game = State.ctx.game
        move_number = request.form.get('move.move', type=int)
        if request.method == 'POST':  # pylint: disable=too-many-nested-blocks
            if request.form.get('btnblanko'):
                if (
                    (coord := request.form.get('coord'))
                    and (char := request.form.get('char'))
                    and (char.isalpha() or char == '_')
                ):
                    char = char.lower()
                    ApiServer.last_msg = f'set blanko: {coord} = {char}'
                    logger.info(ApiServer.last_msg)
                    command_queue.put_nowait(Command(set_blankos, State.ctx.game, coord, char, State.ctx.op_event))
                else:
                    ApiServer.last_msg = 'invalid character for blanko'
                    logger.warning(ApiServer.last_msg)
            elif request.form.get('btnblankodelete'):
                if coord := request.form.get('coord'):
                    ApiServer.last_msg = f'delete blanko: {coord}'
                    logger.info(ApiServer.last_msg)
                    command_queue.put_nowait(Command(remove_blanko, State.ctx.game, coord, State.ctx.op_event))
            elif request.form.get('btninsmoves'):
                logger.debug('in btninsmove')
                if move_number and (0 < move_number <= len(game.moves)):
                    ApiServer.last_msg = f'insert two exchanges before move# {move_number}'
                    logger.info(ApiServer.last_msg)
                    command_queue.put_nowait(Command(admin_insert_moves, State.ctx.game, move_number, State.ctx.op_event))
                else:
                    ApiServer.last_msg = f'invalid move {move_number}'
                    logger.warning(ApiServer.last_msg)
            elif request.form.get('btndelchallenge') and move_number:
                ApiServer.last_msg = f'delete challenge {move_number=}'
                logger.info(ApiServer.last_msg)
                command_queue.put_nowait(Command(admin_del_challenge, State.ctx.game, move_number, State.ctx.op_event))
            elif request.form.get('btntogglechallenge') and move_number:
                ApiServer.last_msg = f'toggle challenge type on move {move_number}'
                logger.info(ApiServer.last_msg)
                command_queue.put_nowait(Command(admin_toggle_challenge_type, State.ctx.game, move_number, State.ctx.op_event))
            elif request.form.get('btninswithdraw') and move_number:
                ApiServer.last_msg = f'insert withdraw for move {move_number}'
                logger.info(ApiServer.last_msg)
                command_queue.put_nowait(
                    Command(admin_ins_challenge, State.ctx.game, move_number, MoveType.WITHDRAW, State.ctx.op_event)
                )
            elif request.form.get('btninschallenge') and move_number:
                ApiServer.last_msg = f'insert invalid challenge for move {move_number}'
                logger.info(ApiServer.last_msg)
                command_queue.put_nowait(
                    Command(admin_ins_challenge, State.ctx.game, move_number, MoveType.CHALLENGE_BONUS, State.ctx.op_event)
                )
            elif request.form.get('btnmove'):
                if move_number and (0 < move_number <= len(game.moves)):
                    move_type = request.form.get('move.type')
                    coord = request.form.get('move.coord')
                    word = request.form.get('move.word')
                    word = word.upper().replace(' ', '_') if word else ''
                    logger.debug(f'{move_type=} {coord=} {word=}')

                    move = game.moves[move_number]
                    if move_type == MoveType.REGULAR.name and coord is not None and word is not None:
                        vert, (col, row) = move.calc_coord(coord)
                        if re.compile('[A-ZÜÄÖ_\\.]+').fullmatch(word):  # valide word
                            command_queue.put_nowait( Command( admin_change_move,
                                    State.ctx.game, move_number, MoveType.REGULAR, (col, row), vert, word, State.ctx.op_event
                                ))  # fmt: off
                            ApiServer.last_msg = f'edit move #{move_number}: {move.type.name} => {move_type}'
                            logger.info(ApiServer.last_msg)
                        else:
                            ApiServer.last_msg = f'invalid character in word {word}'
                            logger.info(ApiServer.last_msg)
                    elif move_type == MoveType.EXCHANGE.name:
                        command_queue.put_nowait(
                            Command(admin_change_move, State.ctx.game, move_number, MoveType.EXCHANGE, event=State.ctx.op_event)
                        )
                        ApiServer.last_msg = f'change move {move_number} to exchange'
                        logger.info(ApiServer.last_msg)
                    else:
                        ApiServer.last_msg = f'change move {move_number} missing parameter {move_type=} {coord=} {word=}'
                        logger.info(ApiServer.last_msg)
                else:
                    logger.warning(f'invalid move number {move_number}')
            return redirect('/moves')
        # fall through: request.method == 'GET':
        (player1, player2) = game.nicknames
        blankos = (
            [
                (get_coord(key), tile)
                for key, tile in game.moves[-1].board.items()
                if tile.letter.islower() or tile.letter == '_'
            ]
            if game.moves
            else []
        )
        return render_template(
            'moves.html', apiserver=ApiServer, player1=player1, player2=player2, move_list=game.moves, blanko_list=blankos
        )

    @staticmethod
    @app.route('/button', methods=['POST', 'GET'])
    def do_buttons():
        """button control"""
        if request.method == 'POST':  # pylint: disable=too-many-nested-blocks
            if request.form.get('GREEN'):
                State.press_button('GREEN')
            elif request.form.get('RED'):
                State.press_button('RED')
            elif request.form.get('YELLOW'):
                State.press_button('YELLOW')
            elif request.form.get('RESET'):
                State.press_button('RESET')
            return redirect('/button')
        _, (time0, time1), _ = ScrabbleWatch.status()  # pylint: disable=duplicate-code
        minutes, seconds = divmod(abs(1800 - time0), 60)
        left = f'-{minutes:1d}:{seconds:02d}' if 1800 - time0 < 0 else f'{minutes:02d}:{seconds:02d}'
        minutes, seconds = divmod(abs(1800 - time1), 60)
        right = f'-{minutes:1d}:{seconds:02d}' if 1800 - time1 < 0 else f'{minutes:02d}:{seconds:02d}'
        return render_template('button.html', apiserver=ApiServer, state=State.ctx.current_state, left=left, right=right)

    @staticmethod
    @app.route('/end_game', methods=['POST', 'GET'])
    def do_end_game():
        """end current game"""
        State.do_end_of_game()
        return redirect('/index')

    @staticmethod
    @app.route('/new_game', methods=['POST', 'GET'])
    def do_new_game():
        """start new game game"""
        if State.ctx.current_state not in (GameState.EOG, GameState.START):
            State.do_end_of_game()
        State.do_new_game()
        return redirect('/index')

    @staticmethod
    @app.route('/settings', methods=['GET', 'POST'])
    def route_settings():
        """display settings on web page"""

        def config_dict() -> dict:
            result = {}
            for each_key, each_val in config.config.items():
                result[each_key] = str(each_val)
            for each_section in config.config.sections():
                for each_key, each_val in config.config.items(each_section):  # type: ignore
                    if each_key not in ('defaults') and each_section not in ('path', 'de', 'en', 'fr'):
                        result[f'{each_section}.{each_key}'] = str(each_val)
            return result

        save_message = ''
        current_config = config_dict()
        if request.method == 'POST' and request.form.get('btnsave'):
            dirty = False
            for key, cval in current_config.items():
                if '.' not in key:
                    continue
                section, option = key.split('.')
                if cval in ('True', 'False'):
                    nval = str(key in request.form)
                else:
                    nval = request.form.get(key, default='')
                if nval and cval != nval:
                    dirty = True
                    config.config.set(section, option, str(nval))
            if dirty:
                config.save()
                current_config = config_dict()
                save_message = 'settings saved'

            dirty = False
            nval = request.form.get('server', default='')
            if nval and nval != upload.upload_config.server:
                dirty = True
                upload.upload_config.server = nval
                logger.debug(f'server = {nval}')
            nval = request.form.get('user', default='')
            if nval and nval != upload.upload_config.user:
                dirty = True
                upload.upload_config.user = nval
                logger.debug(f'user = {nval}')
            nval = request.form.get('password', default='')
            if nval and nval != upload.upload_config.password:
                dirty = True
                upload.upload_config.password = nval
                logger.debug('password changed')
            if dirty:
                upload.upload_config.store()
                save_message = 'settings saved'
            if save_message:
                logger.debug('saved settings')

        return render_template(
            'settings.html',
            apiserver=ApiServer,
            save_message=save_message,
            cfg=current_config,
            server=upload.upload_config.server,
            user=upload.upload_config.user,
        )

    @staticmethod
    @app.route('/wifi', methods=['GET', 'POST'])
    def route_wifi():  # pylint: disable=too-many-branches, too-many-statements
        """set wifi param (ssid, psk) via post request"""

        def wpa_psk(ssid: str, password: str) -> str:
            dk = hashlib.pbkdf2_hmac('sha1', str.encode(password), str.encode(ssid), 4096, 256)
            return binascii.hexlify(dk)[0:64].decode('utf8')

        def run_cmd(cmd: list, log_len=None) -> tuple[int, list]:
            logger.debug(f'{cmd[log_len]=}' if log_len else f'{cmd=}')
            process = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            return process.returncode, process.stdout.splitlines()

        ApiServer._clear_message()
        if request.method == 'POST':
            logger.debug(f'request.form: {request.form.keys()}')
            if request.form.get('btnadd'):
                if (ssid := request.form.get('ssid')) and (key := request.form.get('psk')):
                    hashed = wpa_psk(ssid, key)
                    cmd = ['sudo', '-n', '/usr/bin/nmcli', 'device', 'wifi', 'connect', ssid, 'password', hashed]
                    ret, _ = run_cmd(cmd, -1)
                    ApiServer.last_msg = f'configure wifi {ret=}'
                    sleep(2)
                    State.do_new_game()
            elif request.form.get('btnselect'):
                if ssid := request.form.get('selectwifi'):
                    cmd = ['sudo', '-n', '/usr/bin/nmcli', 'connection', 'up', ssid]
                    ret, output = run_cmd(cmd)
                    ApiServer.last_msg = f'select wifi {ret=}; {output=}'
                    sleep(2)
                    State.do_new_game()
            elif request.form.get('btndelete'):
                if ssid := request.form.get('selectwifi'):
                    cmd = ['sudo', '-n', '/usr/bin/nmcli', 'connection', 'delete', 'id', ssid]
                    ret, output = run_cmd(cmd)
                    ApiServer.last_msg = f'delete wifi {ret=}; {output=}'
                    ScrabbleWatch.display.show_ready()
            elif request.form.get('btnscan'):
                ApiServer.last_msg = 'scan wifi'
            elif request.form.get('btnhotspot'):
                State.do_accesspoint()
            logger.info(f'{ApiServer.last_msg}')
            return redirect('/wifi')

        # fall through: request.method == 'GET':
        cmd = ['sudo', '-n', '/usr/bin/nmcli', '-t', '-f', 'NAME,TYPE,DEVICE', 'con', 'show']
        ret, output = run_cmd(cmd)  # NetworkManager configured wifi
        if ret == 0:
            wifi_clist = [line.split(':', 2) for line in filter(None, output)]
            unique_wifi = {n: (t, d) for n, t, d in wifi_clist if t in ('802-11-wireless', '802-11-wireless-security')}
            wifi_configured = [[n, t, d] for n, (t, d) in unique_wifi.items()]
        else:
            wifi_configured = []
        logger.debug(f'{wifi_configured=}')

        cmd = ['sudo', '-n', '/usr/bin/nmcli', '-t', '-f', 'IN-USE,SSID', 'device', 'wifi', 'list', '--rescan', 'yes']
        ret, output = run_cmd(cmd)  # available wifi
        if ret == 0:
            wifi_list = [line.split(':', 1) for line in filter(None, output)]
            unique_wifi = {}
            for in_use, ssid in wifi_list:
                if ssid not in unique_wifi or unique_wifi[ssid] == ' ':
                    unique_wifi[ssid] = in_use if in_use else ' '
            filtered_wifi_list = [[in_use, ssid] for ssid, in_use in unique_wifi.items()]
        else:
            filtered_wifi_list = []
        logger.debug(f'{filtered_wifi_list=}')

        return render_template('wifi.html', apiserver=ApiServer, wifi_list=filtered_wifi_list, wifi_configured=wifi_configured)

    @staticmethod
    @app.route('/delete_logs', methods=['POST', 'GET'])
    def do_delete_logs():
        """delete message logs"""
        ignore_list = [config.path.log_dir / 'messages.log', config.path.log_dir / 'game.log']
        file_list = list(config.path.log_dir.glob('*'))
        file_list = [f for f in file_list if f not in ignore_list]
        # Iterate over the list of filepaths & remove each file.
        logger.info('delete logs')
        for file_path in file_list:
            try:
                file_path.unlink()
            except OSError:  # noqa: PERF203
                logger.error(f'error: {file_path}')
        for filename in ignore_list:
            with filename.open('w', encoding='UTF-8'):
                pass  # empty log file
        return redirect('/index')

    @staticmethod
    @app.route('/delete_recording', methods=['POST', 'GET'])
    def do_delete_recording():
        """delete recording(s)"""

        logger.info('delete recordings')
        file_list = list((config.path.work_dir).glob('*-camera.jpg'))
        for file_path in file_list:
            try:
                file_path.unlink()
            except OSError:  # noqa: PERF203
                logger.error(f'error: {file_path}')
        return redirect(url_for('route_index'))

    @staticmethod
    @app.route('/download_games', defaults={'req_path': ''})
    @app.route('/download_games/<path:req_path>')
    def do_download_games(req_path):
        """download files from web folder"""
        base_path = config.path.web_dir.resolve()
        fullpath = (base_path / req_path).resolve()
        # validate path
        if not str(fullpath).startswith(str(base_path)):
            return abort(404)
        # Return 404 if path doesn't exist
        if not fullpath.exists():
            return abort(404)
        # Check if path is a file and serve
        if fullpath.is_file():
            return send_file(fullpath)
        # read files
        file_objs = sorted([x.name for x in fullpath.iterdir()])
        return render_template('download_games.html', files=file_objs, apiserver=ApiServer)

    @staticmethod
    @app.route('/download_logs', methods=['POST', 'GET'])
    def do_download_logs():
        """download message logs"""
        from zipfile import ZipFile

        with ZipFile(f'{config.path.log_dir}/log.zip', 'w') as _zip:
            files = ['game.log', 'messages.log']
            for filename in files:
                if (config.path.log_dir / filename).exists():
                    _zip.write(f'{config.path.log_dir}/{filename}')
        return send_from_directory(f'{config.path.log_dir}', 'log.zip', as_attachment=True)

    @staticmethod
    @app.route('/restart', methods=['POST', 'GET'])
    def do_restart():
        """restart app"""
        logger.info('**** Restart application ****')
        config.config.set('system', 'quit', 'restart')  # set temporary restart app
        alarm(1)
        return redirect(url_for('route_index'))

    @staticmethod
    @app.route('/end', methods=['POST', 'GET'])
    def do_end():
        """end app"""
        logger.info('**** Exit application ****')
        config.config.set('system', 'quit', 'end')  # set temporary end app
        alarm(1)
        return redirect(url_for('route_index'))

    @staticmethod
    @app.route('/reboot', methods=['POST', 'GET'])
    def do_reboot():
        """process reboot"""
        logger.info('**** System reboot ****')
        config.config.set('system', 'quit', 'reboot')  # set temporary reboot
        State.do_reboot()
        alarm(2)
        return redirect(url_for('route_index'))

    @staticmethod
    @app.route('/shutdown', methods=['POST', 'GET'])
    def do_shutdown():
        """process reboot"""
        logger.info('**** System shutdown ****')
        config.config.set('system', 'quit', 'shutdown')  # set temporary shutdown
        State.do_reboot()
        alarm(2)
        return redirect(url_for('route_index'))

    @staticmethod
    @app.route('/test_display')
    def do_test_display():
        """start simple display test"""

        if State.ctx.current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            logger.debug('run display test')
            ScrabbleWatch.display.show_boot()
            sleep(0.5)
            ScrabbleWatch.display.show_cam_err()
            sleep(0.5)
            ScrabbleWatch.display.show_ftp_err()
            sleep(0.5)
            ScrabbleWatch.display.show_ready()
            sleep(0.5)
            ApiServer.flask_shutdown_blocked = False
            logger.info('>>> display_test ended')
        else:
            logger.warning('>>> not in State START')
        return redirect(url_for('route_index'))

    @staticmethod
    @app.route('/test_analyze')
    def do_test_analyze():  # pylint: disable=too-many-locals
        """start simple analyze test"""
        from analyzer import ANALYZE_THREADS, analyze
        from customboard import filter_image
        from scrabble import board_to_string

        if State.ctx.current_state in (GameState.START, GameState.EOG, GameState.P0, GameState.P1):
            log_message = 'run analyze test'

            ApiServer.flask_shutdown_blocked = True
            logger.info(log_message)

            img = camera.cam.read(peek=True)

            start = perf_counter()
            warped, warped_gray = warp_image(img)
            _, tiles_candidates = filter_image(warped)

            board = {}
            board = analyze(warped_gray, board, tiles_candidates)
            logger.info(f'analyze took {(perf_counter() - start):.4f} sec(s). ({ANALYZE_THREADS} threads)')

            logger.info(f'\n{board_to_string(board)}')
            # find log
            process = subprocess.run(
                ['tail', '-300', f'{config.path.log_dir}/messages.log'],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            log_out = process.stdout
            if (f := log_out.rfind(log_message)) > 0:
                log_out = log_out[f + len(log_message) :]
            # create b64 image
            _, im_buf_arr = cv2.imencode('.jpg', overlay_grid(warped))
            png_overlay = base64.b64encode(bytes(im_buf_arr))

            ApiServer.flask_shutdown_blocked = False
            return render_template('analyze.html', apiserver=ApiServer, log=log_out, img_data=urllib.parse.quote(png_overlay))
        logger.warning('not in State START, EOG, P0, P1')
        return redirect(url_for('route_index'))

    @staticmethod
    @app.route('/test_upload')
    def do_test_upload():
        """is ftp accessible"""

        logger.info('test upload config entries')
        if upload.upload_config.server is None:
            logger.info('  no server entry found')
        if upload.upload_config.user in (None, ''):
            logger.info('  no user entry found')
        if upload.upload_config.password in (None, ''):
            logger.info('  no password entry found')

        try:
            if upload.upload.upload_status():
                logger.info('upload success')
            else:
                logger.warning('upload = False')
        except OSError as oops:
            logger.error(f'http: I/O error({oops.errno}): {oops.strerror}')
        return redirect(url_for('route_index'))

    @staticmethod
    @app.route('/test_led')
    def do_test_led():
        """start simple led test"""
        from hardware.led import LED, LEDEnum

        if State.ctx.current_state == 'START':
            ApiServer.flask_shutdown_blocked = True
            logger.debug('run LED test')
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
            LED.switch_on(set())
            ApiServer.flask_shutdown_blocked = False
            logger.info('led_test ended')
        else:
            logger.info('not in State START')
        return redirect(url_for('route_index'))

    @staticmethod
    @app.route('/vpn', defaults={'op': 'status'})
    @app.route('/vpn/<path:op>')
    def do_vpn(op):
        """install vpn ops (start, stop, status, install, auth, uninstall)"""
        ops = {
            'status': 'STATUS',
            'install': 'INSTALL',
            'start': 'UP',
            'stop': 'DOWN',
            'auth': 'REAUTH',
            'uninstall': 'UNINSTALL',
        }
        tailscale_cmd = str((config.path.src_dir.parent.parent / 'scripts' / 'tailscale.sh').resolve())
        log_file = str(config.path.log_dir / 'messages.log')
        if op in ops:  # pylint: disable=consider-iterating-dictionary
            cmd = f'{tailscale_cmd} {ops[op]} | tee -a {log_file} &'
            _ = subprocess.run(['bash', '-c', cmd], check=False)
        else:
            logger.warning('invalid operation for vpn')
        ApiServer.tailscale = Path('/usr/bin/tailscale').is_file()
        return redirect(url_for('route_index'))

    @staticmethod
    @app.route('/upgrade_scrabscrap')
    def do_update_scrabscrap():
        """start scrabscrap upgrade"""
        from hardware.led import LED, LEDEnum

        if State.ctx.current_state == 'START':
            LED.blink_on({LEDEnum.yellow})
            ScrabbleWatch.display.show_ready(('Update...', 'pls wait'))
            upgrade_cmd = str((config.path.src_dir.parent.parent / 'scripts' / 'tailscale.sh').resolve())
            log_file = str(config.path.log_dir / 'messages.log')
            os.system(f'{upgrade_cmd} {config.system.gitbranch} | tee -a {log_file} &')
            return redirect(url_for('route_index'))
        logger.warning('not in State START')
        return redirect(url_for('route_index'))

    @sock.route('/ws_log')
    @staticmethod
    def ws_log(sock):  # pylint: disable=no-self-argument
        """websocket for logging"""
        import html

        f = (config.path.log_dir / 'messages.log').open(encoding='utf-8')  # pylint: disable=consider-using-with
        # with will close at eof
        tmp = '\n' + ''.join(f.readlines()[-600:])  # first read last 600 lines
        tmp = html.escape(tmp)
        sock.send(tmp)  # type: ignore[no-member] # pylint: disable=no-member
        while True:
            tmp = f.readline()
            if tmp and tmp != '':  # new data available
                try:
                    tmp = html.escape(tmp)
                    sock.send(tmp)  # type: ignore[no-member] # pylint: disable=no-member
                except ConnectionClosed:
                    f.close()
                    return
            else:
                sleep(0.5)

    @staticmethod
    @app.route('/status', methods=['POST', 'GET'])
    @app.route('/game_status', methods=['POST', 'GET'])
    def game_status():
        """get request to current game state"""
        return State.ctx.game.json_str(), 201

    @sock.route('/ws_status')
    @staticmethod
    def echo(sock):  # pylint: disable=no-self-argument
        """websocket endpoint"""
        logger.debug('call /ws_status')
        while True:
            if State.ctx.op_event.is_set():
                State.ctx.op_event.clear()
            _, (clock1, clock2), _ = ScrabbleWatch.status()
            clock1 = config.scrabble.max_time - clock1
            clock2 = config.scrabble.max_time - clock2
            jsonstr = State.ctx.game.json_str()
            # logger.debug(f'send socket {State.ctx.current_state} clock1 {clock1} clock2: {clock2}')
            try:
                if (
                    State.ctx.current_state in [GameState.S0, GameState.S1, GameState.P0, GameState.P1]
                ) and State.ctx.picture is not None:
                    _, im_buf_arr = cv2.imencode('.jpg', State.ctx.picture)  # type: ignore
                    png_output = base64.b64encode(bytes(im_buf_arr))
                    # logger.debug('b64encode')
                    sock.send(  # type:ignore[no-member] # pylint: disable=no-member
                        f'{{"op": "{State.ctx.current_state}", '
                        f'"clock1": {clock1},"clock2": {clock2}, "image": "{png_output}", "status": {jsonstr}  }}'
                    )
                else:
                    sock.send(  # type: ignore[no-member] # pylint: disable=no-member
                        f'{{"op": "{State.ctx.current_state}", "clock1": {clock1},"clock2": {clock2}, "status": {jsonstr}  }}'
                    )
            except ConnectionClosed:
                logger.debug('connection closed /ws_status')
                return
            State.ctx.op_event.wait()

    def start_server(self, host: str = '0.0.0.0', port=5050, simulator=False):
        """start flask server"""
        logger.info('start api server')
        # flask log only error
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        ApiServer.simulator = simulator
        ApiServer.tailscale = Path('/usr/bin/tailscale').is_file()

        version_flag: str = '\u2757' if version.git_dirty else ''
        branch = '' if version.git_branch == 'main' else version.git_branch
        ApiServer.scrabscrap_version = f'{branch} {version_flag}{version.git_version}'

        if (config.path.src_dir / 'static' / 'webapp' / 'index.html').exists():
            ApiServer.local_webapp = True
        self.app.config['DEBUG'] = False
        self.app.config['TESTING'] = False
        self.server = make_server(host=host, port=port, threaded=True, app=self.app)  # pylint: disable=attribute-defined-outside-init
        self.ctx = self.app.app_context()  # pylint: disable=attribute-defined-outside-init
        self.ctx.push()
        self.server.serve_forever()

    def stop_server(self):
        """stop flask server"""
        logger.info(f'server shutdown blocked: {ApiServer.flask_shutdown_blocked} ... waiting')
        for _ in range(50):  # wait max 5s
            if not ApiServer.flask_shutdown_blocked:
                self.server.shutdown()
                return
            sleep(0.1)
        logger.warning('flask_shutdown_blocked: shutdown timeout')
        self.server.shutdown()


def main():
    """main for standalone test"""
    # for testing
    from threading import Event

    from hardware.camera import switch_camera

    logging.config.fileConfig(
        fname=f'{config.path.work_dir}/log.conf',
        disable_existing_loggers=False,
        defaults={'level': 'DEBUG', 'format': '%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'},
    )

    # set Mock-Display
    ScrabbleWatch.display = Display()

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
