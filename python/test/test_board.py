'''
 This file is part of the scrabble-scraper-v2 distribution
 (https://github.com/scrabscrap/scrabble-scraper-v2)
 Copyright (c) 2023 Rainer Rohloff.

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, version 3.

 This program is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.
'''
import unittest

from game_board import board


class BoardTestCase(unittest.TestCase):
    '''Test class for board.py'''

    def setUp(self) -> None:
        self.counter = 0
        return super().setUp()

    def test_board(self):
        self.assertEqual(board.calc_x_position(200), 3)
        self.assertEqual(board.calc_y_position(100), 1)
        self.assertEqual(board.get_x_position(0), 25)
        self.assertEqual(board.get_y_position(0), 25)
        self.assertEqual(board.get_x_position(3), 175)
        self.assertEqual(board.get_y_position(4), 225)
        self.assertEqual(board.get_x_position(14), 725)
        self.assertEqual(board.get_y_position(14), 725)
        self.assertEqual(board.calc_x_position(board.get_x_position(0)), 0)
        self.assertEqual(board.calc_x_position(board.get_x_position(3)), 3)
        self.assertEqual(board.calc_x_position(board.get_x_position(14)), 14)


if __name__ == '__main__':
    unittest.main(module='test_board')
