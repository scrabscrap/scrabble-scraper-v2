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
import csv
import logging
import logging.config
import os
import unittest
from time import sleep
import glob

from hardware.camera_thread import Camera, CameraEnum
from config import config

TEST_DIR = os.path.dirname(__file__)

FILES = None
# if you want to execute a specific test, replace FILES with an array of *.ini filenames
# FILES = ['test/game12/game.ini']

logging.config.fileConfig(fname=f'{os.path.dirname(os.path.abspath(__file__))}/test_log.conf',
                          disable_existing_loggers=False)


class GameRunnerTestCase(unittest.TestCase):
    """Test class for some scrabble games"""

    def config_setter(self, section: str, option: str, value):
        """set scrabble config"""
        from config import config

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
        return super().setUp()

    def tearDown(self) -> None:
        config.is_testing = False
        return super().tearDown()

    def test_games(self):
        """Test csv games"""
        from display import Display
        from scrabblewatch import ScrabbleWatch
        from state import State
        from config import config

        files = glob.glob(f'{TEST_DIR}/*/game.ini') if FILES is None else FILES
        watch = ScrabbleWatch(Display)
        cam = Camera(use_camera=CameraEnum.FILE)
        State.cam = cam
        State.watch = watch

        for file in files:
            # read *.ini
            test_config = configparser.ConfigParser()
            try:
                with open(f'{file}', 'r', encoding="UTF-8") as config_file:
                    test_config.read_file(config_file)
            except IOError as oops:
                logging.error(f'read ini-file: I/O error({oops.errno}): {oops.strerror}')
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
            logging.info(f'{config.video_warp}: {config.video_warp_coordinates}')
            self.config_setter('board', 'layout', test_config.get('default', 'layout', fallback='custom'))
            cam.stream.formatter = formatter  # type: ignore
            cam.stream.cnt = 1  # type: ignore
            State.cam = cam
            State.do_new_game()
            State.game.nicknames = (name1, name2)

            with self.subTest(csvfile):
                State.press_button(start_button.upper())  # green begins

                # run test: loop csv
                with open(csvfile, mode='r') as csv_file:
                    logging.info(f'TESTFILE: {csvfile}')
                    csv_reader = csv.DictReader(csv_file, skipinitialspace=True)
                    for row in csv_reader:
                        logging.info(f'TEST: {row}')
                        cam.stream.cnt = int(row["Move"])  # type: ignore
                        State.press_button(row["Button"].upper())
                        if State.last_submit is not None:
                            while not State.last_submit.done():  # type: ignore
                                sleep(0.1)

                        self.assertEqual(row["State"].upper(), State.current_state,
                                         f'invalid state {State.current_state} at move {int(row["Move"])}')
                        if State.current_state not in ('P0', 'P1'):
                            self.assertEqual(int(row["Points"]), State.game.moves[-1].points,
                                             f'invalid points {State.game.moves[-1].points} at move {int(row["Move"])}')
                            self.assertEqual(int(row["Score1"]), State.game.moves[-1].score[0],
                                             f'invalid score 1 {State.game.moves[-1].score[0]} at move {int(row["Move"])}')
                            self.assertEqual(int(row["Score2"]), State.game.moves[-1].score[1],
                                             f'invalid score 2 {State.game.moves[-1].score[1]} at move {int(row["Move"])}')
                            self.assertEqual(row["Word"], State.game.moves[-1].word,
                                             f'invalid word {State.game.moves[-1].word} at move {int(row["Move"])}')
                    State.do_end_of_game()
        logging.info('### end of tests ###')
        for file in files:
            logging.info(f'{file}')


# unit tests per commandline
if __name__ == '__main__':
    unittest.main(module='test_gamerunner')
