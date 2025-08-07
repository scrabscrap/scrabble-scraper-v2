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
import binascii
import configparser
import hashlib
import json
import logging
import subprocess
import urllib.parse
from time import sleep

import cv2
import numpy as np
from flask import Blueprint, Request, flash, redirect, render_template, request

from admin.server_context import ctx
from config import config
from customboard import get_last_warp
from game_board.board import overlay_grid
from hardware import camera
from processing import warp_image
from scrabblewatch import ScrabbleWatch
from state import State
from utils import upload

logger = logging.getLogger()
admin_settings_bp = Blueprint('admin_settings', __name__)


def handle_cam_post(form):
    """process post request"""
    if form.get('btndelete'):
        config.config.remove_option('video', 'warp_coordinates')
        config.save()
    elif form.get('btnstore'):
        if 'video' not in config.config.sections():
            config.config.add_section('video')
        config.config.set('video', 'warp_coordinates', form.get('warp_coordinates'))
        config.save()
    return redirect('/cam')


def update_warp_coordinates_from_args(args):
    """ "set warp coordinates from args (admin frontend mouse coordinates)"""
    if len(args.keys()) > 0:
        coord = list(args.keys())[0]
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
            'video', 'warp_coordinates', np.array2string(rect, formatter={'float_kind': lambda x: f'{x:.1f}'}, separator=',')
        )


@admin_settings_bp.route('/cam', methods=['GET', 'POST'])
def route_cam():  # pylint: disable=too-many-branches
    """display current camera picture"""
    if request.method == 'POST':
        return handle_cam_post(request.form)
    update_warp_coordinates_from_args(request.args)
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
        apiserver=ctx,
        img_data=urllib.parse.quote(png_output),
        warp_data=urllib.parse.quote(png_overlay),
        warp_coord=urllib.parse.quote(warp_coord),
        warp_coord_raw=warp_coord,
        warp_coord_cnf=warp_coord_cnf,
    )


def update_loglevel(new_level: int):
    """update log configuration"""
    root_logger = logging.getLogger()
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


def update_recording(recording: bool):
    """update config value for development-recording setting"""
    if config.development.recording != recording:
        logger.info(f'development.recording changed to {recording}')
        if 'development' not in config.config.sections():
            config.config.add_section('development')
        config.config.set('development', 'recording', str(recording))
        config.save()


@admin_settings_bp.route('/loglevel', methods=['GET', 'POST'])
def route_loglevel():
    """settings loglevel, recording"""

    if request.method == 'POST':
        try:
            new_level = request.form.get('loglevel', type=int)
            if new_level is not None:
                update_loglevel(new_level)
            update_recording('recording' in request.form)
        except OSError as oops:
            logger.error(f'I/O error({oops.errno}): {oops.strerror}')
            return redirect('/index')
        return redirect('/loglevel')

    # GET-Request
    loglevel = logging.getLogger().getEffectiveLevel()
    return render_template('loglevel.html', apiserver=ctx, recording=f'{config.development.recording}', loglevel=f'{loglevel}')


def config_dict() -> dict:
    """Erstellt ein Dictionary aller relevanten Konfigurationswerte."""
    result = {}
    for each_key, each_val in config.config.items():
        result[each_key] = str(each_val)
    for each_section in config.config.sections():
        for each_key, each_val in config.config.items(each_section):  # type: ignore
            if each_key not in ('defaults') and each_section not in ('path', 'de', 'en', 'fr'):
                result[f'{each_section}.{each_key}'] = str(each_val)
    return result


def update_config_from_form(current_config: dict, form) -> bool:
    """Aktualisiert die Konfiguration basierend auf dem Formular und gibt zurück, ob etwas geändert wurde."""
    dirty = False
    for key, cval in current_config.items():
        if '.' not in key:
            continue
        section, option = key.split('.')
        if cval in ('True', 'False'):
            nval = str(key in form)
        else:
            nval = form.get(key, default='')
        if nval and cval != nval:
            dirty = True
            config.config.set(section, option, str(nval))
    if dirty:
        config.save()
    return dirty


def update_upload_config_from_form(form) -> bool:
    """Aktualisiert die Upload-Konfiguration und gibt zurück, ob etwas geändert wurde."""
    dirty = False
    nval = form.get('server', default='')
    if nval and nval != upload.upload_config.server:
        dirty = True
        upload.upload_config.server = nval
        logger.debug(f'server = {nval}')
    nval = form.get('user', default='')
    if nval and nval != upload.upload_config.user:
        dirty = True
        upload.upload_config.user = nval
        logger.debug(f'user = {nval}')
    nval = form.get('password', default='')
    if nval and nval != upload.upload_config.password:
        dirty = True
        upload.upload_config.password = nval
        logger.debug('password changed')
    if dirty:
        upload.upload_config.store()
    return dirty


@admin_settings_bp.route('/settings', methods=['GET', 'POST'])
def route_settings():
    """display settings on web page"""
    save_message = ''
    current_config = config_dict()
    if request.method == 'POST' and request.form.get('btnsave'):
        config_dirty = update_config_from_form(current_config, request.form)
        upload_dirty = update_upload_config_from_form(request.form)
        if config_dirty or upload_dirty:
            flash_and_log('settings saved')
        return redirect('/settings')
        # Nach dem Speichern aktuelle Werte neu laden
        # current_config = config_dict()
    if request.method == 'POST' and request.form.get('btnreset'):
        with config.ini_path.open(mode='w', encoding='UTF-8') as _:
            flash_and_log('reset settings')
            config.reload()
        return redirect('/settings')
    return render_template(
        'settings.html',
        apiserver=ctx,
        save_message=save_message,
        cfg=current_config,
        server=upload.upload_config.server,
        user=upload.upload_config.user,
    )


def flash_and_log(msg: str) -> None:
    """flash and log message"""
    flash(message=msg)
    logger.info(msg)


def wpa_psk(ssid: str, password: str) -> str:
    """calculate an encoded wpa psk"""
    dk = hashlib.pbkdf2_hmac('sha1', str.encode(password), str.encode(ssid), 4096, 256)
    return binascii.hexlify(dk)[0:64].decode('utf8')


def run_cmd(cmd: list, log_len=None) -> tuple[int, list]:
    """run a subprocess and catch output"""
    logger.debug(f'{cmd[log_len]=}' if log_len else f'{cmd=}')
    process = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return process.returncode, process.stdout.splitlines()


def handle_add_wifi(req: Request):
    """add a wifi"""
    ssid = req.form.get('ssid')
    key = req.form.get('psk')
    if ssid and key:
        hashed = wpa_psk(ssid, key)
        cmd = ['sudo', '-n', '/usr/bin/nmcli', 'device', 'wifi', 'connect', ssid, 'password', hashed]
        ret, _ = run_cmd(cmd, -1)
        flash_and_log(f'configure wifi {ret=}')
        sleep(2)
        State.do_new_game()


def handle_select_wifi(req: Request):
    """select a wifi"""
    ssid = req.form.get('selectwifi')
    if ssid:
        cmd = ['sudo', '-n', '/usr/bin/nmcli', 'connection', 'up', ssid]
        ret, output = run_cmd(cmd)
        flash_and_log(f'select wifi {ret=}; {output=}')
        sleep(2)
        State.do_new_game()


def handle_delete_wifi(req: Request):
    """delete a configured wifi"""
    ssid = req.form.get('selectwifi')
    if ssid:
        cmd = ['sudo', '-n', '/usr/bin/nmcli', 'connection', 'delete', 'id', ssid]
        ret, output = run_cmd(cmd)
        flash_and_log(f'delete wifi {ret=}; {output=}')
        ScrabbleWatch.display.show_ready()


def get_configured_wifi():
    """get configured wifis"""
    cmd = ['sudo', '-n', '/usr/bin/nmcli', '-t', '-f', 'NAME,TYPE,DEVICE', 'con', 'show']
    ret, output = run_cmd(cmd)
    if ret == 0:
        wifi_clist = [line.split(':', 2) for line in filter(None, output)]
        unique_wifi = {n: (t, d) for n, t, d in wifi_clist if t in ('802-11-wireless', '802-11-wireless-security')}
        return [[n, t, d] for n, (t, d) in unique_wifi.items()]
    return []


def parse_wifi_output(output: list[str]) -> list[list[str]]:
    """Hilfsfunktion: Parsed die Ausgabe von nmcli."""
    wifi_list = [line.split(':', 1) for line in filter(None, output)]
    unique_wifi: dict[str, str] = {}
    for in_use, ssid in wifi_list:
        if ssid not in unique_wifi or unique_wifi[ssid] == ' ':
            unique_wifi[ssid] = in_use if in_use else ' '
    return [[in_use, ssid] for ssid, in_use in unique_wifi.items()]


def get_available_wifi():
    """scan for available wifis"""
    cmd = ['sudo', '-n', '/usr/bin/nmcli', '-t', '-f', 'IN-USE,SSID', 'device', 'wifi', 'list', '--rescan', 'yes']
    ret, output = run_cmd(cmd)
    if ret != 0:
        return []
    return parse_wifi_output(output)


@admin_settings_bp.route('/wifi', methods=['GET', 'POST'])
def route_wifi():
    """set wifi param (ssid, psk) via post request"""
    if request.method == 'POST':
        logger.debug(f'request.form: {request.form.keys()}')
        if request.form.get('btnadd'):
            handle_add_wifi(request)
        elif request.form.get('btnselect'):
            handle_select_wifi(request)
        elif request.form.get('btndelete'):
            handle_delete_wifi(request)
        elif request.form.get('btnscan'):
            flash_and_log('scan wifi')
        elif request.form.get('btnhotspot'):
            State.do_accesspoint()
        return redirect('/wifi')

    wifi_configured = get_configured_wifi()
    logger.debug(f'{wifi_configured=}')
    filtered_wifi_list = get_available_wifi()
    logger.debug(f'{filtered_wifi_list=}')
    return render_template('wifi.html', apiserver=ctx, wifi_list=filtered_wifi_list, wifi_configured=wifi_configured)
