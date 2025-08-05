"""
This file is part of the scrabble-scraper-v2 distribution
(https://github.com/scrabscrap/scrabble-scraper-v2)
Copyright (c) 2020 Rainer Rohloff.

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
import unittest
from pathlib import Path

from move import Tile, gcg_to_coord
from state import State
from test.test_base import BaseTestClass

TEST_DIR = Path(__file__).resolve().parent


class MockGameRunnerTest(BaseTestClass):
    """Test GameRunner without _image_processing"""

    def _dev_string_to_dict(self, csvfile: Path) -> list[dict]:
        data_list = []
        with open(csvfile, mode='r') as f:
            csv_reader = csv.DictReader(f, skipinitialspace=True)
            for row in csv_reader:
                data_list.append(row)
        return data_list

    def _word_to_tiles(self, coord_str: str, word: str) -> dict:
        vertical, start = gcg_to_coord(coord_str)
        dcol, drow = (0, 1) if vertical else (1, 0)
        board = {}
        for c in word:
            if c.isalpha():
                board[start] = Tile(c, 90)
            if c == '_':
                board[start] = Tile(c, 75)
            start = (start[0] + dcol, start[1] + drow)
        return board

    def read_csv(self, f: Path) -> list:
        """convert csv to run data"""
        data_list = self._dev_string_to_dict(f)
        data = []
        for m in data_list:
            next = self._word_to_tiles(m['Coord'], m['Word'])
            data.append({'button': m['Button'].upper(), 'score': (int(m['Score1']), int(m['Score2'])), 'tiles': next})
        return data

    def test_game01(self):
        data = self.read_csv(TEST_DIR / 'game01' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(377, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(374, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game02(self):
        data = self.read_csv(TEST_DIR / 'game02' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(501, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(421, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game03(self):
        data = self.read_csv(TEST_DIR / 'game03' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(323, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(432, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game04(self):
        data = self.read_csv(TEST_DIR / 'game04' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(425, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(362, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game05(self):
        data = self.read_csv(TEST_DIR / 'game05' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(416, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(344, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game06(self):
        data = self.read_csv(TEST_DIR / 'game06' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(438, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(379, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game07(self):
        data = self.read_csv(TEST_DIR / 'game07' / 'game.csv')
        # at move 7 tile '_' will be changed to 'A'
        tiles = data[6]['tiles']
        tiles.update({(4, 10): Tile(letter='A', prob=90)})
        data[6]['tiles'] = tiles

        self.run_data(start_button='green', data=data)
        self.assertEqual(197, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(208, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game08(self):
        data = self.read_csv(TEST_DIR / 'game08' / 'game.csv')
        self.run_data(start_button='green', data=data)
        self.assertEqual(197, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(208, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game12(self):
        data = self.read_csv(TEST_DIR / 'game12' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(185, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(208, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game13(self):
        data = self.read_csv(TEST_DIR / 'game13' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(273, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(452, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game14(self):
        data = self.read_csv(TEST_DIR / 'game14' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(375, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(322, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game15(self):
        data = self.read_csv(TEST_DIR / 'game15' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(323, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(354, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')

    def test_game16(self):
        data = self.read_csv(TEST_DIR / 'game16' / 'game.csv')
        self.run_data(start_button='red', data=data)
        self.assertEqual(463, State.ctx.game.moves[-1].score[0], f'invalid score 1 {State.ctx.game.moves[-1].score[0]}')
        self.assertEqual(418, State.ctx.game.moves[-1].score[1], f'invalid score 2 {State.ctx.game.moves[-1].score[1]}')


if __name__ == '__main__':
    unittest.main(module='test_mock_gamerunner')
