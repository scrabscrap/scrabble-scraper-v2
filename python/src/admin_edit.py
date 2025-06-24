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

import logging
import re

from flask import Blueprint, flash, redirect, render_template, request

from admin_server_context import ctx
from processing import (
    admin_change_move,
    admin_del_challenge,
    admin_ins_challenge,
    admin_insert_moves,
    admin_toggle_challenge_type,
    remove_blanko,
    set_blankos,
)
from scrabble import MoveType
from state import State
from threadpool import Command, command_queue

logger = logging.getLogger(__name__)
admin_edit_bp = Blueprint('admin_edit', __name__)


def flash_and_log(msg: str) -> None:
    """flash flask und log to info"""
    flash(message=msg)
    logger.info(msg)


def get_coord(_coord, is_vertical=False) -> str:
    """transform to gcg coordinates"""
    (_col, _row) = _coord
    return str(_col + 1) + chr(ord('A') + _row) if is_vertical else chr(ord('A') + _row) + str(_col + 1)


def is_blanko(char: str | None = None) -> bool:
    """is char a blanko"""
    return char is not None and (char.isalpha() or char == '_')


def handle_btnblanko(form, game):
    """handle button set blanko"""
    coord = form.get('coord')
    char = form.get('char')
    if coord and is_blanko(char):
        char = char.lower()
        flash_and_log(f'set blanko: {coord} = {char}')
        command_queue.put_nowait(Command(set_blankos, game, coord, char, State.ctx.op_event))
    else:
        flash_and_log('invalid character for blanko')


def handle_btnblankodelete(form, game):
    """handle blanko delete"""
    coord = form.get('coord')
    if coord:
        flash_and_log(f'delete blanko: {coord}')
        command_queue.put_nowait(Command(remove_blanko, game, coord, State.ctx.op_event))


def handle_btninsmoves(game, move_number):
    """handle insert exchange moves"""
    logger.debug('in btninsmove')
    if move_number and (0 < move_number <= len(game.moves)):
        flash_and_log(f'insert two exchanges before move# {move_number}')
        command_queue.put_nowait(Command(admin_insert_moves, game, move_number, State.ctx.op_event))
    else:
        flash_and_log(f'invalid move {move_number}')


def handle_btndelchallenge(game, move_number):
    """handle delete challenge"""
    flash_and_log(f'delete challenge {move_number=}')
    command_queue.put_nowait(Command(admin_del_challenge, game, move_number, State.ctx.op_event))


def handle_btntogglechallenge(game, move_number):
    """handle toggle challange type"""
    flash_and_log(f'toggle challenge type on move {move_number}')
    command_queue.put_nowait(Command(admin_toggle_challenge_type, game, move_number, State.ctx.op_event))


def handle_btninswithdraw(game, move_number):
    """handle insert withdraw"""
    flash_and_log(f'insert withdraw for move {move_number}')
    command_queue.put_nowait(Command(admin_ins_challenge, game, move_number, MoveType.WITHDRAW, State.ctx.op_event))


def handle_btninschallenge(game, move_number):
    """handle insert challenge"""
    flash_and_log(f'insert invalid challenge for move {move_number}')
    command_queue.put_nowait(Command(admin_ins_challenge, game, move_number, MoveType.CHALLENGE_BONUS, State.ctx.op_event))


WORD_PATTERN = re.compile(r'[A-ZÜÄÖ_\.]+')


def is_valid_word(word: str) -> bool:
    """is word valid"""
    return bool(WORD_PATTERN.fullmatch(word))


def handle_btnmove(form, game, move_number):
    """handle button change move"""
    if move_number < 0 or move_number >= len(game.moves):
        flash_and_log(f'invalid move number {move_number}')
        return

    move_type = form.get('move.type')
    coord = form.get('move.coord')
    word = form.get('move.word')
    word = word.upper().replace(' ', '_') if word else ''
    logger.debug(f'{move_type=} {coord=} {word=}')
    move = game.moves[move_number]

    if move_type == MoveType.REGULAR.name:
        if coord is None or word is None:
            flash_and_log(f'change move {move_number} missing parameter {move_type=} {coord=} {word=}')
            return
        try:
            vert, (col, row) = move.calc_coord(coord)
        except Exception as e:  # pylint: disable=broad-exception-caught
            flash_and_log(f'error parsing coord {coord}: {e}')
            return
        if not is_valid_word(word):
            flash_and_log(f'invalid character in word {word}')
            return
        command_queue.put_nowait(
            Command(admin_change_move, game, move_number, MoveType.REGULAR, (col, row), vert, word, State.ctx.op_event)
        )
        flash_and_log(f'edit move #{move_number}: {move_type}: {word}')
    elif move_type == MoveType.EXCHANGE.name:
        command_queue.put_nowait(Command(admin_change_move, game, move_number, MoveType.EXCHANGE, event=State.ctx.op_event))
        flash_and_log(f'change move {move_number} to exchange')
    else:
        flash_and_log(f'change move {move_number} missing parameter {move_type=} {coord=} {word=}')


@admin_edit_bp.route('/moves', methods=['GET', 'POST'])
def route_moves():  # pylint: disable=too-many-locals,too-many-statements
    """edit moves form"""

    game = State.ctx.game
    move_number = request.form.get('move.move', type=int)
    if request.method == 'POST':
        form = request.form
        if form.get('btnblanko'):
            handle_btnblanko(form, game)
        elif form.get('btnblankodelete'):
            handle_btnblankodelete(form, game)
        elif form.get('btninsmoves'):
            handle_btninsmoves(game, move_number)
        elif form.get('btndelchallenge'):
            handle_btndelchallenge(game, move_number)
        elif form.get('btntogglechallenge'):
            handle_btntogglechallenge(game, move_number)
        elif form.get('btninswithdraw'):
            handle_btninswithdraw(game, move_number)
        elif form.get('btninschallenge'):
            handle_btninschallenge(game, move_number)
        elif form.get('btnmove'):
            handle_btnmove(form, game, move_number)
        return redirect('/moves')

    # GET-Request
    (player1, player2) = game.nicknames
    blankos = (
        [(get_coord(key), tile) for key, tile in game.moves[-1].board.items() if tile.letter.islower() or tile.letter == '_']
        if game.moves
        else []
    )
    return render_template(
        'moves.html', apiserver=ctx, player1=player1, player2=player2, move_list=game.moves, blanko_list=blankos
    )
