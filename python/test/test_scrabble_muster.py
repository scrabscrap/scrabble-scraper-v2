"""
 This file is part of the scrabble-scraper distribution
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
import logging.config
import os
import unittest

import cv2
from processing import analyze, filter_candidates, filter_image, warp_image

TEST_DIR = os.path.dirname(__file__)

logging.config.fileConfig(fname=os.path.dirname(os.path.abspath(__file__)) + '/test_log.conf',
                          disable_existing_loggers=True)


class ScrabbleMusterTestCase(unittest.TestCase):

    def config_setter(self, section: str, option: str, value):
        from config import config

        if value is not None:
            if section not in config.config.sections():
                config.config.add_section(section)
            config.config.set(section, option, str(value))
        else:
            config.config.remove_option(section, option)

    def print_board(self, board: dict) -> str:
        result = '  |'
        for i in range(15):
            result += f'{(i + 1):2d} '
        result += ' | '
        for i in range(15):
            result += f'{(i + 1):2d} '
        result += '\n'
        for row in range(15):
            result += f"{chr(ord('A') + row)} |"
            for col in range(15):
                if (col, row) in board:
                    result += f' {board[(col, row)][0]} '
                else:
                    result += ' . '
            result += ' | '
            for col in range(15):
                result += f' {str(board[(col, row)][1])}' if (col, row) in board else ' . '
            result += ' | \n'
        return result

    def setUp(self):
        self.config_setter('output', 'ftp', False)

    def test_names(self):

        files = [TEST_DIR + "/board-tests/board-04.png"]
        for f in files:
            img = cv2.imread(f)
            self.config_setter('video', 'warp_coordinates', None)
            self.config_setter('board', 'layout', 'custom')
            warped = warp_image(img)
            warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
            _, tiles_candidates = filter_image(warped)
            ignore_coords = set()
            filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
            board = {}
            new_board = analyze(warped_gray, board, filtered_candidates)
            print(f'new board= {self.print_board(new_board)}')
            res = {(3, 7): 'A',
                   (4, 7): 'N',
                   (5, 7): 'K',
                   (6, 7): 'E',
                   (7, 7): '_',
                   (8, 7): 'S',
                   (9, 7): 'T',
                   (10, 7): 'E',
                   (11, 7): 'F',
                   (12, 7): 'A',
                   (13, 7): 'N'}
            k = new_board.keys()
            v = new_board.values()
            k1 = [(x, y) for (x, y) in k]
            v1 = [t for (t, p) in v]
            self.assertEqual(dict(zip(*[k1, v1])), res, "Test")

    def test_err_images(self):

        files = [TEST_DIR + "/board-tests/err-01.png", TEST_DIR + "/board-tests/err-02.png",
                 TEST_DIR + "/board-tests/err-03.png",
                 TEST_DIR + "/board-tests/err-04.png", TEST_DIR + "/board-tests/err-05.png",
                 TEST_DIR + "/board-tests/err-06.png",
                 TEST_DIR + "/board-tests/err-07.png", TEST_DIR + "/board-tests/err-08.png",
                 TEST_DIR + "/board-tests/err-09.png",
                 TEST_DIR + "/board-tests/err-10.png", TEST_DIR + "/board-tests/err-11.png",
                 TEST_DIR + "/board-tests/err-12.png",
                 TEST_DIR + "/board-tests/err-14.png",
                 TEST_DIR + "/board-tests/err-16.png", TEST_DIR + "/board-tests/err-17.png",
                 TEST_DIR + "/board-tests/err-18.png",
                 TEST_DIR + "/board-tests/err-19.png", TEST_DIR + "/board-tests/err-20.png",
                 TEST_DIR + "/board-tests/err-21.png",
                 TEST_DIR + "/board-tests/err-22.png",
                 TEST_DIR + "/board-tests/err-24.png"
                 ]
        # Errors on analyze:
        # TEST_DIR + "/board-tests/err-13.png", TEST_DIR + "/board-tests/err-15.png", TEST_DIR + "/board-tests/err-23.png",
        for f in files:
            img = cv2.imread(f)
            self.config_setter('video', 'warp_coordinates', None)
            self.config_setter('board', 'layout', 'custom')
            warped = warp_image(img)
            warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
            _, tiles_candidates = filter_image(warped)
            ignore_coords = set()
            filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
            board = {}
            new_board = analyze(warped_gray, board, filtered_candidates)
            print(f'new board= {self.print_board(new_board)}')
            # last_board = ret  # falls der Test vorige Boards berücksichtigen soll
            res = {(4, 11): 'G', (5, 7): 'Y', (5, 10): 'U', (5, 11): 'S', (6, 7): 'L', (6, 10): 'Ü',
                   (7, 7): 'A', (7, 8): 'E', (7, 9): 'E', (7, 10): 'N', (8, 7): 'T', (9, 7): 'Z',
                   (10, 5): 'W', (10, 6): 'Ö', (10, 7): 'I', (10, 8): 'U', (10, 9): 'Ä'}
            k = new_board.keys()
            v = new_board.values()
            k1 = [(x, y) for (x, y) in k]
            v1 = [t for (t, p) in v]
            self.assertEqual(dict(zip(*[k1, v1])), res, f'Test error: {f}')

    def test_new_images(self):

        files = [TEST_DIR + "/board-tests/board-00.png", TEST_DIR + "/board-tests/board-01.png",
                 TEST_DIR + "/board-tests/board-03.png"]

        for f in files:
            img = cv2.imread(f)
            self.config_setter('video', 'warp_coordinates', None)
            self.config_setter('board', 'layout', 'custom')
            warped = warp_image(img)
            warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
            _, tiles_candidates = filter_image(warped)
            ignore_coords = set()
            filtered_candidates = filter_candidates((7, 7), tiles_candidates, ignore_coords)
            board = {}
            new_board = analyze(warped_gray, board, filtered_candidates)
            print(f'new board= {self.print_board(new_board)}')

            res = {(5, 7): 'V', (6, 6): 'M', (6, 7): 'Ä', (6, 8): 'Y',
                   (6, 9): 'X', (7, 7): 'L', (7, 9): 'G', (8, 7): 'S',
                   (8, 9): 'A', (8, 10): 'Ü', (8, 11): 'T'}
            k = new_board.keys()
            v = new_board.values()
            k1 = [(x, y) for (x, y) in k]
            v1 = [t for (t, p) in v]
            self.assertEqual(dict(zip(*[k1, v1])), res, f'Test error: {f}')


# unit tests per commandline
if __name__ == '__main__':
    unittest.main()
