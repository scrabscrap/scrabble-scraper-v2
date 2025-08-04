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

import unittest

from move import MoveType, Tile
from processing import admin_change_move
from state import State
from test.test_base import BaseTestClass


class AlgorithmAdminTestCase(BaseTestClass):
    """Test class for algorithm"""

    def test_141(self):
        """Test 141 - Algorithm: change tile via admin call - first move"""
        # H4 FIRNS
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': {  (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                               (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), }, 
                 }
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        game = State.ctx.game
        # admin call
        admin_change_move(game, 0, MoveType.REGULAR, (5, 7), False, word='RNS')
        self.assertEqual((6, 0), game.moves[-1].score, 'invalid scores')

    def test_142(self):
        """Test 142 - Algorithm: 2 moves on board correct first move"""
        # H4 FIRNS
        # 5G V.TEn
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (24, 18),
                   'tiles': { (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)},
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        game = State.ctx.game
        # admin call
        admin_change_move(game, 0, MoveType.REGULAR, (4, 7), False, word='IRNS')
        self.assertEqual((8, 18), game.moves[-1].score, 'invalid scores')

    def test_143(self):
        """Test 143 - Algorithm: 2 moves on board correct second move"""
        # H4 FIRNS
        # 5G V.TEn
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (24, 18),
                   'tiles': { (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)},
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        game = State.ctx.game

        # admin call
        move_number = 1
        col = 4
        row = 7
        admin_change_move(game, move_number, MoveType.REGULAR, (col, row), True, word='ITEN')
        self.assertEqual((24, 8), game.moves[-1].score, 'invalid scores')

    def test_144(self):
        """Test 144 - Algorithm: 2 moves on board correct first move"""
        # H4 FIRNS
        # 5G V.TEn
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (24, 18),
                   'tiles': { (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)},
                 }
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        game = State.ctx.game
        # admin call
        move_number = 0
        col = 3
        row = 7
        admin_change_move(game, move_number, MoveType.REGULAR, (col, row), False, word='FIRNS')
        self.assertEqual((24, 18), game.moves[-1].score, 'invalid scores')

    def test_145(self):
        """Test 145 - Algorithm: change tile to exchange via admin call - first move"""
        # H4 FIRNS
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        game = State.ctx.game
        # admin call
        move_number = 0
        admin_change_move(game, int(move_number), MoveType.EXCHANGE)
        self.assertEqual((0, 0), game.moves[-1].score, 'invalid scores')

    def test_146(self):
        """replace blanko with lower character"""
        # H4 TURNeNS
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
                              (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        score1 = State.ctx.game.moves[-1].score

        # H4 TURNeNS
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
                              (7, 7): Tile('e', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        score2 = State.ctx.game.moves[-1].score
        self.assertEqual(score1, score2, 'same score with _ and e expected')


if __name__ == '__main__':
    unittest.main(module='test_algorithm_admin')
