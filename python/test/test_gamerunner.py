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
from time import sleep

from config import config
from customboard import clear_last_warp
from display import Display
from hardware import camera
from scrabble import MoveRegular
from scrabblewatch import ScrabbleWatch
from state import GameState, State
from utils.threadpool import command_queue

TEST_DIR = os.path.dirname(__file__)
logging.config.fileConfig(fname=f'{os.path.dirname(os.path.abspath(__file__))}/test_log.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


class GameRunnerTestCase(unittest.TestCase):
    """Test class for some scrabble games"""

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
        return super().tearDown()

    def test_game01(self):
        self.run_game(file=f'{TEST_DIR}/game01/scrabble.ini')

    def test_game02(self):
        self.run_game(file=f'{TEST_DIR}/game02/scrabble.ini')

    def test_game03(self):
        self.run_game(file=f'{TEST_DIR}/game03/scrabble.ini')

    def test_game04(self):
        self.run_game(file=f'{TEST_DIR}/game04/scrabble.ini')

    def test_game05(self):
        self.run_game(file=f'{TEST_DIR}/game05/scrabble.ini')

    def test_game06(self):
        self.run_game(file=f'{TEST_DIR}/game06/scrabble.ini')

    def test_game07(self):
        self.run_game(file=f'{TEST_DIR}/game07/scrabble.ini')

    def test_game08(self):
        self.run_game(file=f'{TEST_DIR}/game08/scrabble.ini')

    def test_game12(self):
        self.run_game(file=f'{TEST_DIR}/game12/scrabble.ini')

    def test_game13(self):
        self.run_game(file=f'{TEST_DIR}/game13/scrabble.ini')

    def test_game14(self):
        self.run_game(file=f'{TEST_DIR}/game14/scrabble.ini')

    def test_game15(self):
        # test: wrong end of game
        # move 39 Green exchange
        # YELLOW - EOG => must insert move 40
        # correct flow:
        # move 39, "Green", "S1", "-", , 0, 329, 336
        # move 40, "Red", "S0", "5D", ".I.", 12, 329, 348
        # YELLOW - EOG
        # check log output !
        self.run_game(file=f'{TEST_DIR}/game15/scrabble.ini')

    def test_game16(self):
        self.run_game(file=f'{TEST_DIR}/game16/scrabble.ini')

    def test_pause_remove(self):
        self.run_game(file=f'{TEST_DIR}/test-pause-remove/scrabble.ini')

    def test_game2023dm01(self):
        self.run_game(file=f'{TEST_DIR}/game2023DM-01/scrabble.ini')

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
            if State.ctx.current_state != GameState.EOG:
                State.do_end_of_game()

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
    unittest.main(module='test_gamerunner')
