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
import logging
import subprocess
import urllib.parse
from time import perf_counter, sleep

import cv2
from flask import Blueprint, redirect, render_template, url_for

import upload
from admin_server_context import ctx
from config import config
from game_board.board import overlay_grid
from hardware import camera
from processing import warp_image
from scrabblewatch import ScrabbleWatch
from state import GameState, State

logger = logging.getLogger()
admin_test_bp = Blueprint('admin_test', __name__)


@admin_test_bp.route('/test_display')
def do_test_display():
    """start simple display test"""

    if State.ctx.current_state == 'START':
        ctx.flask_shutdown_blocked = True
        logger.debug('run display test')
        ScrabbleWatch.display.show_boot()
        sleep(0.5)
        ScrabbleWatch.display.show_cam_err()
        sleep(0.5)
        ScrabbleWatch.display.show_ftp_err()
        sleep(0.5)
        ScrabbleWatch.display.show_ready()
        sleep(0.5)
        ctx.flask_shutdown_blocked = False
        logger.info('>>> display_test ended')
    else:
        logger.warning('>>> not in State START')
    return redirect(url_for('route_index'))


@admin_test_bp.route('/test_analyze')
def do_test_analyze():  # pylint: disable=too-many-locals
    """start simple analyze test"""
    from analyzer import ANALYZE_THREADS, analyze
    from customboard import filter_image
    from scrabble import board_to_string

    if State.ctx.current_state in (GameState.START, GameState.EOG, GameState.P0, GameState.P1):
        log_message = 'run analyze test'

        ctx.flask_shutdown_blocked = True
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

        ctx.flask_shutdown_blocked = False
        return render_template('analyze.html', apiserver=ctx, log=log_out, img_data=urllib.parse.quote(png_overlay))
    logger.warning('not in State START, EOG, P0, P1')
    return redirect(url_for('route_index'))


@admin_test_bp.route('/test_upload')
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


@admin_test_bp.route('/test_led')
def do_test_led():
    """start simple led test"""
    from hardware.led import LED, LEDEnum

    if State.ctx.current_state == 'START':
        ctx.flask_shutdown_blocked = True
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
        ctx.flask_shutdown_blocked = False
        logger.info('led_test ended')
    else:
        logger.info('not in State START')
    return redirect(url_for('route_index'))
