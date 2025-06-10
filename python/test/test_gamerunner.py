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

import configparser
import cProfile
import csv
import linecache
import logging
import logging.config
import os
import tracemalloc
import unittest
from pstats import Stats
from time import sleep

from config import config
from hardware import camera
from scrabble import MoveRegular
from state import GameState
from threadpool import command_queue

PROFILE = False
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
        from processing import clear_last_warp

        config.is_testing = True
        clear_last_warp()
        self.config_setter('output', 'upload_server', False)
        self.config_setter('development', 'recording', False)
        if PROFILE:
            self.pr = cProfile.Profile()
            self.pr.enable()
        return super().setUp()

    def tearDown(self) -> None:
        config.is_testing = False
        if PROFILE:
            p = Stats(self.pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()
        return super().tearDown()

    def test_game01(self):
        self.run_game(file=f'{TEST_DIR}/game01/game.ini')

    def test_game02(self):
        self.run_game(file=f'{TEST_DIR}/game02/game.ini')

    def test_game03(self):
        self.run_game(file=f'{TEST_DIR}/game03/game.ini')

    def test_game04(self):
        self.run_game(file=f'{TEST_DIR}/game04/game.ini')

    def test_game05(self):
        self.run_game(file=f'{TEST_DIR}/game05/game.ini')

    def test_game06(self):
        self.run_game(file=f'{TEST_DIR}/game06/game.ini')

    def test_game07(self):
        self.run_game(file=f'{TEST_DIR}/game07/game.ini')

    def test_game08(self):
        self.run_game(file=f'{TEST_DIR}/game08/game.ini')

    def test_game12(self):
        self.run_game(file=f'{TEST_DIR}/game12/game.ini')

    def test_game13(self):
        self.run_game(file=f'{TEST_DIR}/game13/game.ini')

    def test_game14(self):
        self.run_game(file=f'{TEST_DIR}/game14/game.ini')

    def test_game15(self):
        # test: wrong end of game
        # move 39 Green exchange
        # YELLOW - EOG => must insert move 40
        # correct flow:
        # move 39, "Green", "S1", "-", , 0, 329, 336
        # move 40, "Red", "S0", "5D", ".I.", 12, 329, 348
        # YELLOW - EOG
        # check log output !
        self.run_game(file=f'{TEST_DIR}/game15/game.ini')

    def test_game16(self):
        self.run_game(file=f'{TEST_DIR}/game16/game.ini')

    def test_pause_remove(self):
        self.run_game(file=f'{TEST_DIR}/test-pause-remove/game.ini')

    def test_game2023dm01(self):
        self.run_game(file=f'{TEST_DIR}/game2023DM-01/game.ini')

    def display_top(self, snapshot, key_type='lineno', limit=10):
        snapshot = snapshot.filter_traces(
            (tracemalloc.Filter(False, '<frozen importlib._bootstrap_external>'), tracemalloc.Filter(False, 'xx<unknown>'))
        )
        top_stats = snapshot.statistics(key_type)

        print('Top %s lines' % limit)
        for index, stat in enumerate(top_stats[:limit], 1):
            frame = stat.traceback[0]
            print('#%s: %s:%s: %.1f KiB' % (index, frame.filename, frame.lineno, stat.size / 1024))
            line = linecache.getline(frame.filename, frame.lineno).strip()
            if line:
                print('    %s' % line)

        other = top_stats[limit:]
        if other:
            size = sum(stat.size for stat in other)
            print('%s other: %.1f KiB' % (len(other), size / 1024))
        total = sum(stat.size for stat in top_stats)
        print('Total allocated size: %.1f KiB' % (total / 1024))

    def run_game(self, file: str):
        """Test csv games"""
        import tracemalloc

        from display import Display
        from scrabblewatch import ScrabbleWatch
        from state import State

        if PROFILE:
            tracemalloc.start()
            tracemalloc.reset_peak()

        ScrabbleWatch.display = Display()
        camera.switch_camera('file')

        # read *.ini
        test_config = configparser.ConfigParser()
        try:
            with open(f'{file}', 'r', encoding='UTF-8') as config_file:
                test_config.read_file(config_file)
        except IOError as oops:
            logger.error(f'read ini-file: I/O error({oops.errno}): {oops.strerror}')
            self.fail(f'error reading ini-file {file}')

        name1 = test_config.get('default', 'name1', fallback='Name1')
        name2 = test_config.get('default', 'name2', fallback='Name2')
        warp = test_config.getboolean('default', 'warp', fallback=True)
        start_button = test_config.get('default', 'start', fallback='Red')

        coordstr = test_config.get('default', 'warp-coord', fallback=None)
        formatter = f'{os.path.dirname(config_file.name)}/{test_config.get("default", "formatter")}'  # type: ignore
        csvfile = f'{os.path.dirname(config_file.name)}/game.csv'  # type: ignore

        # set config
        self.config_setter('video', 'warp', warp)
        self.config_setter('video', 'warp_coordinates', coordstr)
        logger.info(f'{config.video.warp}: {config.video.warp_coordinates}')
        self.config_setter('board', 'layout', test_config.get('default', 'layout', fallback='custom'))
        camera.cam.formatter = formatter  # type: ignore
        camera.cam.counter = 1  # type: ignore
        camera.cam.resize = False  # type: ignore
        State.do_new_game()
        State.ctx.game.nicknames = (name1, name2)
        State.press_button(start_button.upper())  # green begins

        # run test: loop csv
        with open(csvfile, mode='r') as csv_file:
            logger.info(f'TESTFILE: {csvfile}')
            csv_reader = csv.DictReader(csv_file, skipinitialspace=True)
            for row in csv_reader:
                logger.info(f'TEST: {row}')
                camera.cam.counter = int(row['Move'])  # type: ignore
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
                    if isinstance(State.ctx.game.moves[-1], (MoveRegular)):
                        self.assertEqual(
                            row['Word'],
                            State.ctx.game.moves[-1].word,
                            f'invalid word {State.ctx.game.moves[-1].word} at move {int(row["Move"])}',
                        )
                logger.warning(f'qsize={command_queue.qsize()}')
            if State.ctx.current_state != GameState.EOG:
                State.do_end_of_game()
        logger.info(f'### end of tests {file} ###')
        if PROFILE:
            snapshot = tracemalloc.take_snapshot()
            self.display_top(snapshot, limit=10)
            second_size, second_peak = tracemalloc.get_traced_memory()
            print(f'{second_size=}, {second_peak=}')

            top_stats = snapshot.statistics('traceback')
            stat = top_stats[0]
            print('%s memory blocks: %.1f KiB' % (stat.count, stat.size / 1024))
            for line in stat.traceback.format():
                print(line)


# unit tests per commandline
if __name__ == '__main__':
    unittest.main(module='test_gamerunner')
