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

import csv
import logging
import logging.config
import os
import unittest
from pathlib import Path
from time import sleep

from config import config
from customboard import clear_last_warp
from display import Display
from hardware import camera
from move import MoveType
from processing import admin_change_move, admin_insert_moves
from scrabble import MoveRegular
from scrabblewatch import ScrabbleWatch
from state import GameState, State
from utils.threadpool import command_queue

TEST_DIR = os.path.dirname(__file__)
logging.config.fileConfig(fname=f'{os.path.dirname(os.path.abspath(__file__))}/test_log.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


class AdminEditTestCase(unittest.TestCase):
    """Test class for admin edit scrabble games"""

    def config_setter(self, section: str, option: str, value):
        """set scrabble config"""

        if value is not None:
            if section not in config.config.sections():
                config.config.add_section(section)
            config.config.set(section, option, str(value))
        else:
            config.config.remove_option(section, option)

    def setUp(self):
        config.is_testing = True
        clear_last_warp()
        self.config_setter('output', 'upload_server', False)
        self.config_setter('development', 'recording', False)
        logging.disable(logging.DEBUG)  # nur Info Ausgaben
        return super().setUp()

    def tearDown(self) -> None:
        config.is_testing = False
        # config.reload(str(config.path.work_dir / 'scrabble.ini'))
        State.do_end_of_game()
        return super().tearDown()

    def test_edit01(self):
        # Move, Button, State, Coord, Word, Points, Score1, Score2
        # 1, "Red", "S0", "-", , 0, 0, 0
        # 2, "Green", "S1", "H7", "QI", 22, 22, 0
        # 3, "Red", "S0", "9C", "GRUNDS", 22, 22, 22
        # 4, "Green", "S1", "I6", "BI", 17, 39, 22
        # 5, "Red", "S0", "J7", "SPUREN_", 73, 39, 95
        # 6, "Green", "S1", "5I", "OHA", 16, 55, 95
        # 7, "Red", "S0", "11H", "CR.W", 18, 55, 113
        # 8, "Green", "S1", "D7", "EI.E", 5, 60, 113

        self.run_game(file=f'{TEST_DIR}/edit01/scrabble.ini')
        msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in State.ctx.game.moves)
        logger.info(f'Game State with error\n{msg}')
        admin_insert_moves(State.ctx.game, index=4)
        msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in State.ctx.game.moves)
        logger.info(f'after insert moves\n{msg}')
        # edit: 5I OHA
        admin_change_move(State.ctx.game, index=4, movetype=MoveType.REGULAR, coord=(4, 8), isvertical=True, word='OHA')
        msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in State.ctx.game.moves)
        logger.info(f'after edit 5I OHA\n{msg}')
        # edit: 11H CR(E)W - calculate D7 EI(R)E
        admin_change_move(State.ctx.game, index=5, movetype=MoveType.REGULAR, coord=(10, 7), isvertical=True, word='CREW')
        msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in State.ctx.game.moves)
        logger.info(f'after edit 11H CREW\n{msg}')
        logger.info(f'final board\n{State.ctx.game.board_str()}')
        self.assertEqual(60, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(133, State.ctx.game.moves[-1].score[1], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')

    def test_edit02(self):
        # Move, Button, State, Coord, Word, Points, Score1, Score2
        # 0, "Green", "S1", "H4", "FIRNS", 24, 24, 0
        # 1, "Red", "S0", "5G", "V.TEN", 20, 24, 20
        # 2, "Green", "S1", "J2", "MÖS.", 19, 43, 20
        # 3, "Red", "S0", "3I", "K.DER", 38, 43, 58
        # 4, "Green", "S1", "-", "", 0, 43, 58
        # 5, "Red", "S0", "N1", "WANK", 34, 43, 92

        self.run_game(file=f'{TEST_DIR}/edit02/scrabble.ini')
        msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in State.ctx.game.moves)
        logger.info(f'Game State with error\n{msg}')
        logger.info(f'final board\n{State.ctx.game.board_str()}')
        # edit: J2 MÖS.
        admin_change_move(State.ctx.game, index=2, movetype=MoveType.REGULAR, coord=(1, 9), isvertical=False, word='MÖSE')
        msg = '\n' + ''.join(f'{mov.move:2d} {mov.gcg_str}\n' for mov in State.ctx.game.moves)
        logger.info(f'after edit J2 MÖS.\n{msg}')
        logger.info(f'final board\n{State.ctx.game.board_str()}')
        self.assertEqual(43, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(92, State.ctx.game.moves[-1].score[1], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')

    def run_game(self, file: str):
        """Test csv games"""

        config.reload(ini_file=file, clean=True)
        start_button = config.test.start
        csvfile = f'{os.path.dirname(file)}/game.csv'
        logger.info(f'{config.video.warp=}: {config.video.warp_coordinates=}')

        ScrabbleWatch.display = Display()
        camera.switch_camera('file')
        if isinstance(camera.cam, camera.CameraFile):
            camera.cam.formatter = config.development.simulate_path
            camera.cam.counter = 1
            camera.cam.resize = False
        if not Path(config.development.simulate_path.format(1)).is_file():  # check for first file
            self.skipTest('Image File not available')
        State.do_new_game()
        State.ctx.game.nicknames = (config.test.name1, config.test.name2)
        State.press_button(start_button.upper())
        self._run_csv_test(csvfile)

    def _run_csv_test(self, csvfile):
        with open(csvfile, mode='r') as csv_file:
            logger.info(f'TESTFILE: {csvfile}')
            csv_reader = csv.DictReader(csv_file, skipinitialspace=True)
            for row in csv_reader:
                self._process_csv_row(row)

    def _process_csv_row(self, row):
        logger.info(f'TEST: {row}')
        camera.cam.counter = int(row['Move'])  # type:ignore
        State.press_button(row['Button'].upper())
        sleep(0.01)

        self.assertEqual(
            GameState[row['State'].upper()],
            State.ctx.current_state,
            f'invalid state {State.ctx.current_state} at move {int(row["Move"])}',
        )

        if State.ctx.current_state not in (GameState.P0, GameState.P1, GameState.EOG):
            command_queue.join()
            self.assertEqual(
                int(row['Points']),
                State.ctx.game.moves[-1].points,
                f'invalid points {State.ctx.game.moves[-1].points} at move {int(row["Move"])}',
            )
            self.assertEqual(
                int(row['Score1']),
                State.ctx.game.moves[-1].score[0],
                f'invalid score 1 {State.ctx.game.moves[-1].score[0]} at move {int(row["Move"])}',
            )
            self.assertEqual(
                int(row['Score2']),
                State.ctx.game.moves[-1].score[1],
                f'invalid score 2 {State.ctx.game.moves[-1].score[1]} at move {int(row["Move"])}',
            )
            if isinstance(State.ctx.game.moves[-1], MoveRegular):
                self.assertEqual(
                    row['Word'],
                    State.ctx.game.moves[-1].word,
                    f'invalid word {State.ctx.game.moves[-1].word} at move {int(row["Move"])}',
                )
        logger.debug(f'qsize={command_queue.qsize()}')


# unit tests per commandline
if __name__ == '__main__':
    unittest.main(module='test_admin_edit')
