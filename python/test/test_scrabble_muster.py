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

import logging
import logging.config
import os
import sys
import unittest

import cv2

from config import config
from processing import analyze, filter_candidates, filter_image, warp_image

TEST_DIR = os.path.dirname(__file__)

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, force=True, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'
)


class ScrabbleMusterTestCase(unittest.TestCase):
    """Testclass for some board pattern"""

    def config_setter(self, section: str, option: str, value):
        """set value in scrabscrap config"""

        if value is not None:
            if section not in config.config.sections():
                config.config.add_section(section)
            config.config.set(section, option, str(value))
        else:
            config.config.remove_option(section, option)

    def print_board(self, board: dict) -> str:
        """print out Scrabble board dictionary"""
        result = '  |'
        for i in range(15):
            result += f'{(i + 1):2d} '
        result += ' | '
        for i in range(15):
            result += f'{(i + 1):2d} '
        result += '\n'
        for row in range(15):
            result += f'{chr(ord("A") + row)} |'
            for col in range(15):
                if (col, row) in board:
                    result += f' {board[(col, row)][0]} '
                else:
                    result += ' · '
            result += ' | '
            for col in range(15):
                result += f' {str(board[(col, row)][1])}' if (col, row) in board else ' · '
            result += ' | \n'
        return result

    def setUp(self):
        from processing import clear_last_warp

        config.is_testing = True
        clear_last_warp()
        self.config_setter('output', 'server_upload', False)
        self.config_setter('video', 'warp', True)
        self.config_setter('video', 'warp_coordinates', None)
        self.config_setter('board', 'layout', 'custom2012')
        self.config_setter('development', 'recording', False)
        return super().setUp()

    def tearDown(self) -> None:
        config.is_testing = False
        return super().tearDown()

    def test_names(self):
        """Test: Namess on board"""
        files = {
            TEST_DIR + '/board2012/board-04.png': {
                (3, 7): 'A',
                (4, 7): 'N',
                (5, 7): 'K',
                (6, 7): 'E',
                (7, 7): '_',
                (8, 7): 'S',
                (9, 7): 'T',
                (10, 7): 'E',
                (11, 7): 'F',
                (12, 7): 'A',
                (13, 7): 'N',
            }
        }

        for file, expected in files.items():
            img = cv2.imread(file)
            logging.debug(f'file: {file}')

            warped, warped_gray = warp_image(img)
            _, tiles_candidates = filter_image(warped)
            # ignore_coords = set()
            # filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
            # ! check all tiles
            filtered_candidates = tiles_candidates
            board = {}
            new_board = analyze(warped_gray, board, filtered_candidates)
            logging.debug(f'new board= \n{self.print_board(new_board)}')

            keys = [(x, y) for (x, y) in new_board.keys()]
            values = [t for (t, p) in new_board.values()]
            self.assertEqual(dict(zip(*[keys, values])), expected, 'Test')

    def test_board2012_chars(self):
        """Regression test: old error images"""
        files = [TEST_DIR + '/board2012/chars.png']
        # files = [
        # ]

        # error
        for file in files:
            img = cv2.imread(file)
            logging.debug(f'file: {file}')

            warped, warped_gray = warp_image(img)
            _, tiles_candidates = filter_image(warped)
            ignore_coords = set()
            filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
            board = {}
            new_board = analyze(warped_gray, board, filtered_candidates)
            logging.debug(f'new board= \n{self.print_board(new_board)}')
            # last_board = ret  # falls der Test vorige Boards berücksichtigen soll
            res = {
                (8, 8): 'W',
                (4, 9): 'Y',
                (4, 6): 'G',
                (5, 7): 'N',
                (7, 9): 'Ö',
                (6, 7): 'O',
                (9, 5): 'F',
                (8, 9): 'Ü',
                (7, 6): 'I',
                (9, 8): 'X',
                (8, 6): 'K',
                (4, 7): 'M',
                (5, 5): 'B',
                (7, 7): 'P',
                (6, 5): 'C',
                (5, 8): 'T',
                (8, 7): 'Q',
                (9, 9): '_',
                (6, 8): 'U',
                (9, 6): 'L',
                (6, 9): 'Ä',
                (4, 5): 'A',
                (5, 6): 'H',
                (4, 8): 'S',
                (6, 6): 'J',
                (5, 9): 'Z',
                (7, 5): 'D',
                (9, 7): 'R',
                (8, 5): 'E',
                (7, 8): 'V',
            }
            keys = new_board.keys()
            values = new_board.values()
            keys1 = [(x, y) for (x, y) in keys]
            values1 = [t for (t, p) in values]
            self.assertEqual(dict(zip(*[keys1, values1])), res, f'Test error: {file}')

    def test_board2012_err(self):
        """Regression test: old error images"""
        files = [
            TEST_DIR + '/board2012/err-01.png',
            TEST_DIR + '/board2012/err-02.png',
            TEST_DIR + '/board2012/err-03.png',
            TEST_DIR + '/board2012/err-04.png',
            TEST_DIR + '/board2012/err-05.png',
            TEST_DIR + '/board2012/err-06.png',
            TEST_DIR + '/board2012/err-07.png',
            TEST_DIR + '/board2012/err-08.png',
            TEST_DIR + '/board2012/err-09.png',
            TEST_DIR + '/board2012/err-10.png',
            # TEST_DIR + "/board2012/err-11.png",
            TEST_DIR + '/board2012/err-12.png',
            TEST_DIR + '/board2012/err-13.png',
            TEST_DIR + '/board2012/err-14.png',
            TEST_DIR + '/board2012/err-15.png',
            TEST_DIR + '/board2012/err-16.png',
            TEST_DIR + '/board2012/err-17.png',
            TEST_DIR + '/board2012/err-18.png',
            TEST_DIR + '/board2012/err-19.png',
            TEST_DIR + '/board2012/err-20.png',
            TEST_DIR + '/board2012/err-21.png',
            TEST_DIR + '/board2012/err-22.png',
            TEST_DIR + '/board2012/err-23.png',
            TEST_DIR + '/board2012/err-24.png',
        ]
        # files = [
        # ]

        # error
        for file in files:
            img = cv2.imread(file)
            logging.debug(f'file: {file}')

            warped, warped_gray = warp_image(img)
            _, tiles_candidates = filter_image(warped)
            ignore_coords = set()
            filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
            board = {}
            new_board = analyze(warped_gray, board, filtered_candidates)
            logging.debug(f'new board= \n{self.print_board(new_board)}')
            # last_board = ret  # falls der Test vorige Boards berücksichtigen soll
            res = {
                (4, 11): 'G',
                (5, 7): 'Y',
                (5, 10): 'U',
                (5, 11): 'S',
                (6, 7): 'L',
                (6, 10): 'Ü',
                (7, 7): 'A',
                (7, 8): 'E',
                (7, 9): 'E',
                (7, 10): 'N',
                (8, 7): 'T',
                (9, 7): 'Z',
                (10, 5): 'W',
                (10, 6): 'Ö',
                (10, 7): 'I',
                (10, 8): 'U',
                (10, 9): 'Ä',
            }
            keys = new_board.keys()
            values = new_board.values()
            keys1 = [(x, y) for (x, y) in keys]
            values1 = [t for (t, p) in values]
            self.assertEqual(dict(zip(*[keys1, values1])), res, f'Test error: {file}')

    def test_board2012(self):
        """Test some board 2012 images"""
        files = {
            TEST_DIR + '/board2012/board-00.png': {
                (5, 7): 'V',
                (6, 6): 'M',
                (6, 7): 'Ä',
                (6, 8): 'Y',
                (6, 9): 'X',
                (7, 7): 'L',
                (7, 9): 'G',
                (8, 7): 'S',
                (8, 9): 'A',
                (8, 10): 'Ü',
                (8, 11): 'T',
            },
            # TEST_DIR + "/board2012/board-01.png": {(5, 7): 'V', (6, 6): 'M', (6, 7): 'Ä', (6, 8): 'Y',
            #                                        (6, 9): 'X', (7, 7): 'L', (7, 9): 'G', (8, 7): 'S',
            #                                        (8, 9): 'A', (8, 10): 'Ü', (8, 11): 'T'},
            # TEST_DIR + "/board2012/board-02.png": {(5, 7): 'V', (6, 6): 'M', (6, 7): 'Ä', (6, 8): 'Y',
            #                                        (6, 9): 'X', (7, 7): 'L', (7, 9): 'G', (8, 7): 'S',
            #                                        (8, 9): 'A', (8, 10): 'Ü', (8, 11): 'T'},
            TEST_DIR + '/board2012/board-03.png': {
                (5, 7): 'V',
                (6, 6): 'M',
                (6, 7): 'Ä',
                (6, 8): 'Y',
                (6, 9): 'X',
                (7, 7): 'L',
                (7, 9): 'G',
                (8, 7): 'S',
                (8, 9): 'A',
                (8, 10): 'Ü',
                (8, 11): 'T',
            },
        }

        for file, expected in files.items():
            img = cv2.imread(file)
            warped, warped_gray = warp_image(img)
            _, tiles_candidates = filter_image(warped)
            # ignore_coords = set()
            # filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
            # ! check all tiles
            filtered_candidates = tiles_candidates
            board = {}
            new_board = analyze(warped_gray, board, filtered_candidates)
            logging.debug(f'new board= \n{self.print_board(new_board)}')

            keys = [(x, y) for (x, y) in new_board.keys()]
            values = [t for (t, p) in new_board.values()]
            self.assertEqual(dict(zip(*[keys, values])), expected, f'Test error: {file}')

    def test_board2020(self):
        """Test some board 2020 images"""

        # todo: new printout - the tests have to be adapted
        files = {
            # TEST_DIR + "/board2020/board-01.png": {},
            TEST_DIR + '/board2020/board-02.jpg': {
                (7, 7): 'E',
                (6, 7): 'W',
                (6, 8): 'I',
                (6, 9): 'R',
                (8, 7): 'R',
                (8, 6): 'Ü',
                (8, 5): 'K',
            },
            TEST_DIR + '/board2020/board-03.jpg': {(7, 7): 'E', (6, 7): 'W', (8, 7): 'R'},
            TEST_DIR + '/board2020/board-04.jpg': {(7, 7): 'E', (6, 7): 'W', (8, 7): 'R', (8, 6): 'Ü', (8, 5): 'K'},
            TEST_DIR + '/board2020/board-05.jpg': {
                (7, 7): 'E',
                (6, 7): 'W',
                (6, 8): 'I',
                (6, 9): 'R',
                (8, 7): 'R',
                (8, 6): 'Ü',
                (8, 5): 'K',
            },
            TEST_DIR + '/board2020/board-06.jpg': {
                (7, 7): 'E',
                (6, 7): 'W',
                (6, 8): 'I',
                (6, 9): 'R',
                (8, 7): 'R',
                (8, 6): 'Ü',
                (8, 5): 'K',
            },
            TEST_DIR + '/board2020/board-07.jpg': {
                (7, 7): 'E',
                (6, 7): 'W',
                (6, 8): 'I',
                (6, 9): 'R',
                (8, 7): 'R',
                (8, 6): 'Ü',
                (8, 5): 'K',
            },
            TEST_DIR + '/board2020/board-08.jpg': {
                (7, 7): 'E',
                (6, 7): 'W',
                (6, 8): 'I',
                (6, 9): 'R',
                (8, 7): 'R',
                (8, 6): 'Ü',
                (8, 5): 'K',
            },
            TEST_DIR + '/board2020/board-09.jpg': {
                (7, 7): 'E',
                (6, 7): 'W',
                (6, 8): 'I',
                (6, 9): 'R',
                (8, 7): 'R',
                (8, 6): 'Ü',
                (8, 5): 'K',
            },
            TEST_DIR + '/board2020/board-10.jpg': {
                (7, 7): 'E',
                (6, 7): 'W',
                (6, 8): 'I',
                (6, 9): 'R',
                (8, 7): 'R',
                (8, 6): 'Ü',
                (8, 5): 'K',
            },
        }

        for file, expected in files.items():
            img = cv2.imread(file)
            self.config_setter('board', 'layout', 'custom2020light')
            logging.debug(f'file: {file}')

            warped, warped_gray = warp_image(img)
            _, tiles_candidates = filter_image(warped)
            # ignore_coords = set()
            # filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
            # ! check all tiles
            filtered_candidates = tiles_candidates
            board = {}
            new_board = analyze(warped_gray, board, filtered_candidates)
            logging.debug(f'new board= \n{self.print_board(new_board)}')

            keys = [(x, y) for (x, y) in new_board.keys()]
            values = [t for (t, p) in new_board.values()]
            self.assertEqual(dict(zip(*[keys, values])), expected, f'Test error: {file}')

    def test_board2012_weak_tiles(self):
        """Test some board 2012 images"""
        files = {
            TEST_DIR + '/board2012/weak-ae-01.jpg': {
                (4, 9): 'G',
                (3, 7): 'D',
                (4, 6): 'F',
                (9, 2): 'R',
                (9, 5): 'K',
                (11, 2): 'D',
                (8, 9): 'S',
                (10, 6): 'E',
                (8, 12): 'P',
                (10, 3): '_',
                (1, 6): 'U',
                (10, 9): 'N',
                (13, 2): 'M',
                (10, 12): 'N',
                (1, 9): 'N',
                (11, 11): 'A',
                (13, 11): 'M',
                (7, 7): 'O',
                (6, 5): 'H',
                (7, 10): 'X',
                (6, 8): 'T',
                (12, 12): 'L',
                (4, 8): 'N',
                (5, 9): 'L',
                (8, 5): 'C',
                (10, 2): 'Ü',
                (0, 7): 'W',
                (10, 5): 'T',
                (11, 10): 'Y',
                (2, 7): 'R',
                (1, 5): 'Q',
                (1, 8): 'E',
                (13, 10): 'R',
                (13, 13): 'R',
                (7, 9): 'I',
                (6, 7): 'R',
                (12, 2): 'E',
                (4, 7): 'A',
                (4, 10): 'T',
                (9, 9): 'E',
                (8, 7): 'M',
                (10, 4): 'Z',
                (9, 12): 'I',
                (8, 10): 'I',
                (10, 1): 'N',
                (10, 7): 'N',
                (11, 12): 'K',
                (10, 10): 'E',
                (1, 7): 'E',
                (13, 9): 'Ä',
                (13, 12): 'E',
                (6, 6): 'Ö',
                (7, 5): 'U',
                (6, 9): 'E',
            }
        }

        for file, expected in files.items():
            img = cv2.imread(file)
            warped, warped_gray = warp_image(img)
            _, tiles_candidates = filter_image(warped)
            filtered_candidates = tiles_candidates
            board = {}
            new_board = analyze(warped_gray, board, filtered_candidates)
            logging.debug(f'new board= \n{self.print_board(new_board)}')

            keys = [(x, y) for (x, y) in new_board.keys()]
            values = [t for (t, p) in new_board.values()]
            self.assertEqual(dict(zip(*[keys, values])), expected, f'Test error: {file}')


# unit tests per commandline
if __name__ == '__main__':
    unittest.main(module='test_scrabble_muster')
