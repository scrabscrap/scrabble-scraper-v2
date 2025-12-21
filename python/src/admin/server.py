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

from __future__ import annotations

import base64
from collections import deque
import json
import logging
import os
import platform
import subprocess
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from signal import alarm
from time import sleep

import cv2
import psutil
from flask import Flask, abort, make_response, redirect, render_template, request, send_file, send_from_directory, url_for
from flask_sock import ConnectionClosed, Sock, Server
from werkzeug.serving import make_server

from admin.checks import admin_test_bp
from admin.edit import admin_edit_bp
from admin.server_context import ctx
from admin.settings import admin_settings_bp
from config import config, version
from hardware.led import LED, LEDEnum
from processing import event_set
from scrabblewatch import ScrabbleWatch
from state import GameState, State

logger = logging.getLogger()
app = Flask(__name__, template_folder=config.path.src_dir / 'templates', static_folder=config.path.src_dir / 'static')
sock = Sock(app)
app.register_blueprint(admin_settings_bp)
app.register_blueprint(admin_edit_bp)
app.register_blueprint(admin_test_bp)
app.secret_key = 'scrabscrap'


@app.route('/webapp/<path:path>')
def static_file(path):
    """static routing for web app on rpi"""
    response = make_response(app.send_static_file(f'webapp/{path}'))
    response.headers['X-WebSocket-Available'] = 'true'
    return response


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def route_index():
    """index web page"""
    if request.method == 'POST':
        if request.form.get('btnplayer'):
            _handle_player_form(request.form)
            return redirect('/index')
        if request.form.get('btntournament'):
            _handle_tournament_form(request.form)
            return redirect('/index')

    player1, player2 = State.ctx.game.nicknames
    tournament = config.scrabble.tournament
    return render_template('index.html', apiserver=ctx, player1=player1, player2=player2, tournament=tournament)


def _handle_player_form(form):
    """handle set player names"""
    player1 = form.get('player1')
    player2 = form.get('player2')
    if player1 and player2 and player1.casefold() != player2.casefold():
        logger.debug(f'set {player1=} / {player2=}')
        State.ctx.game.set_player_names(player1, player2)
        if State.ctx.current_state == GameState.START:
            ScrabbleWatch.display.show_ready((player1, player2))
        event_set(event=State.ctx.op_event)
    else:
        logger.warning(f'can not set: {player1}/{player2}')


def _handle_tournament_form(form):
    """handle set tournament name"""
    tournament = form.get('tournament')
    if tournament and tournament != config.scrabble.tournament:
        if 'scrabble' not in config.config.sections():
            config.config.add_section('scrabble')
        config.config.set('scrabble', 'tournament', str(tournament))
        config.save()
        logger.info(f'set {tournament=}')
    else:
        logger.warning(f'can not set: {tournament=}')


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
    return render_template(
        'button.html',
        apiserver=ctx,
        state=State.ctx.current_state,
        green=LEDEnum.green.value,  # pylint: disable=duplicate-code
        yellow=LEDEnum.yellow.value,
        red=LEDEnum.red.value,
        left=left,
        right=right,
    )


@app.route('/end_game', methods=['POST', 'GET'])
def do_end_game():
    """end current game"""
    State.do_end_of_game()
    return redirect('/index')


@app.route('/new_game', methods=['POST', 'GET'])
def do_new_game():
    """start new game game"""
    if State.ctx.current_state not in (GameState.EOG, GameState.START):
        State.do_end_of_game()
    State.do_new_game()
    return redirect('/index')


@app.route('/logs')
def route_logs():
    """display message log"""
    return render_template('logs.html', apiserver=ctx)


def bytes2human(n):
    """Convert bytes to human-readable string."""
    # http://code.activestate.com/recipes/578019
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if abs(n) >= prefix[s]:
            value = float(n) / prefix[s]
            return f'{value:.1f}{s}'
    return f'{n}B'


def log_process_info():
    """log process infos"""
    logger.info(f'{"=" * 40} Process Info {"=" * 28}')
    for process in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        with suppress(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            if 'python' in process.info['name'].lower():
                logger.info(
                    f'{process.info["pid"]:6} {process.info["name"]} '
                    f'mem:{process.info["memory_percent"]:.2f}% cpu:{process.info["cpu_percent"]:.2f}%'
                )


@app.route('/log_sysinfo', methods=['GET', 'POST'])
def log_sysinfo():  # pylint: disable=too-many-locals,too-many-statements
    """log out system info"""

    _system_info()
    _boot_info()
    _cpu_info()
    _mem_info()
    _disk_info()
    log_process_info()
    _git_info()
    return redirect('/logs')


def _git_info():
    cmd = ['git', 'log', '--oneline', '-n', '20']
    process = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if process.returncode != 0:
        logger.warning(f'git command returned non-zero: {process.returncode}')
    else:
        logger.info(f'{"=" * 40} Git Information {"=" * 25}\n{process.stdout}')


def _disk_info():
    logger.info(f'{"=" * 40} Disk Information {"=" * 24}')
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


def _mem_info():
    logger.info(f'{"=" * 40} Memory Information {"=" * 22}')
    svmem = psutil.virtual_memory()
    logger.info(f'Total: {bytes2human(svmem.total)}')
    logger.info(f'Available: {bytes2human(svmem.available)}')
    logger.info(f'Used: {bytes2human(svmem.used)}')
    logger.info(f'Percentage: {svmem.percent}%')

    logger.info(f'{"=" * 40} SWAP {"=" * 36}')
    swap = psutil.swap_memory()
    logger.info(f'Total: {bytes2human(swap.total)}')
    logger.info(f'Free: {bytes2human(swap.free)}')
    logger.info(f'Used: {bytes2human(swap.used)}')
    logger.info(f'Percentage: {swap.percent}%')


def _cpu_info():
    logger.info(f'{"=" * 40} CPU Info {"=" * 32}')
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


def _boot_info():
    logger.info(f'{"=" * 40} Boot Time {"=" * 31}')
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    logger.info(f'Boot Time: {bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}')


def _system_info():
    logger.info(f'{"=" * 40} System Information {"=" * 22}')
    uname = platform.uname()
    logger.info(f'System: {uname.system}')
    logger.info(f'Node Name: {uname.node}')
    logger.info(f'Release: {uname.release}')
    logger.info(f'Version: {uname.version}')
    logger.info(f'Machine: {uname.machine}')
    logger.info(f'Processor: {uname.processor}')


@app.route('/delete_logs', methods=['POST', 'GET'])
def do_delete_logs():
    """delete message logs"""
    ignore_list = [config.path.log_dir / 'messages.log', config.path.log_dir / 'game.log']
    file_list = list(config.path.log_dir.glob('*.log*'))
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
    return render_template('download_games.html', files=file_objs, apiserver=ctx)


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


@app.route('/restart', methods=['POST', 'GET'])
def do_restart():
    """restart app"""
    logger.info('**** Restart application ****')
    config.config.set('system', 'quit', 'restart')  # set temporary restart app
    alarm(1)
    return redirect(url_for('route_index'))


@app.route('/end', methods=['POST', 'GET'])
def do_end():
    """end app"""
    logger.info('**** Exit application ****')
    config.config.set('system', 'quit', 'end')  # set temporary end app
    alarm(1)
    return redirect(url_for('route_index'))


@app.route('/reboot', methods=['POST', 'GET'])
def do_reboot():
    """process reboot"""
    logger.info('**** System reboot ****')
    config.config.set('system', 'quit', 'reboot')  # set temporary reboot
    State.do_reboot()
    alarm(2)
    return redirect(url_for('route_index'))


@app.route('/shutdown', methods=['POST', 'GET'])
def do_shutdown():
    """process reboot"""
    logger.info('**** System shutdown ****')
    config.config.set('system', 'quit', 'shutdown')  # set temporary shutdown
    State.do_reboot()
    alarm(2)
    return redirect(url_for('route_index'))


@app.route('/vpn', defaults={'op': 'status'})
@app.route('/vpn/<path:op>')
def do_vpn(op):
    """install vpn ops (start, stop, status, install, auth, uninstall)"""
    ops = {'status': 'STATUS', 'install': 'INSTALL', 'start': 'UP', 'stop': 'DOWN', 'auth': 'REAUTH', 'uninstall': 'UNINSTALL'}
    tailscale_cmd = str((config.path.src_dir.parent.parent / 'scripts' / 'tailscale.sh').resolve())
    log_file = str(config.path.log_dir / 'messages.log')
    if op in ops:  # pylint: disable=consider-iterating-dictionary
        cmd = f'{tailscale_cmd} {ops[op]} | tee -a {log_file} &'
        try:
            ret = subprocess.run(['bash', '-c', cmd], check=False)
            if ret.returncode != 0:
                logger.warning(f'vpn command returned non-zero: {ret.returncode}')
        except Exception:
            logger.exception(f'do_vpn: running tailscale command failed for op={op} cmd={cmd}')
    else:
        logger.warning('invalid operation for vpn')
    ctx.tailscale = Path('/usr/bin/tailscale').is_file()
    return redirect(url_for('route_index'))


@app.route('/upgrade_scrabscrap')
def do_update_scrabscrap():
    """start scrabscrap upgrade"""
    if State.ctx.current_state in (GameState.START, GameState.EOG):
        LED.blink_on({LEDEnum.yellow})
        ScrabbleWatch.display.show_ready(('SCRABSCRAP', 'update\u2026'))
        upgrade_cmd = str(config.path.src_dir.parent.parent / 'scripts' / 'upgrade.sh')
        os.system(f'{upgrade_cmd} {config.system.gitbranch} | tee -a {config.path.log_dir}/messages.log &')
        return redirect(url_for('route_index'))
    logger.warning('not in State START')
    return redirect(url_for('route_index'))


@sock.route('/ws_log')
def ws_log(socket):
    """websocket for logging"""
    import html

    try:
        f = (config.path.log_dir / 'messages.log').open(encoding='utf-8')  # pylint: disable=consider-using-with
    except Exception:
        logger.exception(f'ws_log: cannot open messages.log at {config.path.log_dir / "messages.log"}')
        return

    # with will close at eof
    tmp = tmp = '\n' + ''.join(deque(f, maxlen=600))  # first read last 600 lines
    tmp = html.escape(tmp)
    socket.send(tmp)  # type: ignore[no-member] # pylint: disable=no-member
    while True:
        try:
            tmp = f.readline()
            if tmp and tmp != '':  # new data available
                try:
                    tmp = html.escape(tmp)
                    socket.send(tmp)  # type: ignore[no-member] # pylint: disable=no-member
                except ConnectionClosed:
                    f.close()
                    return
            else:
                sleep(0.5)
        except ConnectionClosed:  # noqa: PERF203
            f.close()
            return
        except Exception:  # noqa: PERF203
            logger.exception('ws_log: unexpected failure in websocket loop')
            f.close()
            return


@app.route('/status', methods=['POST', 'GET'])
@app.route('/game_status', methods=['POST', 'GET'])
def game_status():
    """get request to current game state"""
    _, (clock1, clock2), _ = ScrabbleWatch.status()
    clock1 = config.scrabble.max_time - clock1
    clock2 = config.scrabble.max_time - clock2
    jsonstr = State.ctx.game.json_str()
    image_str = f'web/image-{len(State.ctx.game.moves) - 1}.jpg' if State.ctx.game.moves else ''
    return (
        f'{{"op": "{State.ctx.current_state.name}", "clock1": {clock1},"clock2": {clock2}, '
        f'"image": "{image_str}", "status": {jsonstr}  }}',
        201,
    )


@sock.route('/ws_status')
def echo(socket: Server):
    """websocket endpoint"""
    logger.debug('call /ws_status')
    while True:
        if State.ctx.op_event.is_set():
            State.ctx.op_event.clear()

        json_data = State.ctx.game.get_json_data()
        _, (clock1, clock2), _ = ScrabbleWatch.status()
        try:
            img = State.ctx.picture if State.ctx.picture is not None else None
            if State.ctx.game.moves and State.ctx.game.moves[-1].img is not None:
                img = State.ctx.game.moves[-1].img
            if img is not None:
                _, im_buf_arr = cv2.imencode('.jpg', img)  # type: ignore
                image_str = base64.b64encode(im_buf_arr).decode('utf-8')  # type: ignore
                json_data['image'] = f'data:image/png;base64,{image_str}'
            # possible problem: check if state is set before thread ended?
            json_data['state'] = State.ctx.current_state.name
            json_data['clock1'] = config.scrabble.max_time - clock1
            json_data['clock2'] = config.scrabble.max_time - clock2
            socket.send(f'{json.dumps(json_data)}')
        except ConnectionClosed:
            logger.exception('connection closed /ws_status')
            return
        except Exception:
            logger.exception('ws_status: error while preparing/sending status')
            return
        State.ctx.op_event.wait()


def start_server(host: str = '0.0.0.0', port=5050, simulator=False):
    """start flask server"""
    logger.info('start api server')
    # flask log only error
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    ctx.simulator = simulator
    ctx.tailscale = Path('/usr/bin/tailscale').is_file()

    version_flag: str = '\u2757' if version.git_dirty else ''
    branch = '' if version.git_branch == 'main' else version.git_branch
    ctx.scrabscrap_version = f'{branch} {version_flag}{version.git_version}'

    if (config.path.src_dir / 'static' / 'webapp' / 'index.html').exists():
        ctx.local_webapp = True
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    ctx.server = make_server(host=host, port=port, threaded=True, app=app)
    context = app.app_context()
    context.push()
    ctx.server.serve_forever()


def stop_server():
    """stop flask server"""
    logger.info(f'server shutdown blocked: {ctx.flask_shutdown_blocked} ... waiting')
    for _ in range(50):  # wait max 5s
        if not ctx.flask_shutdown_blocked:
            ctx.server.shutdown()  # type: ignore
            return
        sleep(0.1)
    logger.warning('flask_shutdown_blocked: shutdown timeout')
    ctx.server.shutdown()  # type:ignore
