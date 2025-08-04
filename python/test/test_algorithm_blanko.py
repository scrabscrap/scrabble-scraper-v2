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

import numpy as np

from move import BoardType, Tile
from processing import _move_processing, admin_insert_moves, remove_blanko, set_blankos
from state import State
from test.test_base import BaseTestClass


class AlgorithmBlankoTestCase(BaseTestClass):
    """Test class for algorithm"""

    def test_11(self):
        """Test 11 - Algorithm: remove invalid blanks"""

        game = State.ctx.game.new_game()
        board: BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)

        new_board: BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
            (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75),
            (6, 6): Tile('_', 76), (3, 6): Tile('_', 76),
        }  # fmt:off
        new_tiles, _, _ = _move_processing(game=game, board=new_board, previous_board=board)
        self.assertDictEqual(
            new_tiles,
            {(4, 10): Tile('N', 75), (4, 9): Tile('E', 75), (4, 6): Tile('V', 75), (4, 8): Tile('T', 75)},
            'invalid tiles',
        )

        board = new_board.copy()
        new_board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
            (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75),
            (7, 5): Tile('_', 75), (6, 6): Tile('_', 76), (3, 6): Tile('_', 76), (3, 8): Tile('_', 75),
            (7, 8): Tile('A', 75), (7, 9): Tile('N', 75),
            (8, 8): Tile('_', 76), (7, 10): Tile('_', 76),
        }  # fmt:off
        new_tiles, _, _ = _move_processing(game=game, board=new_board, previous_board=board)
        self.assertDictEqual(new_tiles, {(7, 10): Tile('_', 76), (7, 9): Tile('N', 75), (7, 8): Tile('A', 75)}, 'invalid tiles')

        new_board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
            (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75),
            (7, 5): Tile('_', 75), (6, 6): Tile('_', 76), (3, 6): Tile('_', 76), (3, 8): Tile('_', 75),
            (7, 8): Tile('A', 75), (7, 9): Tile('N', 75),
            (7, 11): Tile('_', 76), (7, 10): Tile('_', 76),
        }  # fmt:off
        new_tiles, _, _ = _move_processing(game=game, board=new_board, previous_board=board)
        self.assertDictEqual(
            new_tiles,
            {(7, 11): Tile('_', 76), (7, 10): Tile('_', 76), (7, 9): Tile('N', 75), (7, 8): Tile('A', 75)},
            'invalid tiles',
        )

        new_board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
            (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75),
            (7, 8): Tile('A', 75), (7, 9): Tile('N', 75),
            (7, 11): Tile('_', 76), (7, 10): Tile('_', 76),
        }  # fmt:off
        new_tiles, _, _ = _move_processing(game=game, board=new_board, previous_board=board)
        self.assertDictEqual(
            new_tiles,
            {(7, 11): Tile('_', 76), (7, 10): Tile('_', 76), (7, 9): Tile('N', 75), (7, 8): Tile('A', 75)},
            'invalid tiles',
        )

    def test_147(self):
        """replace blanko with lower character"""
        # H4 FIRNS
        # 5G V.TEn
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (24, 18),
                   'tiles': {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)},
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        game = State.ctx.game
        score1 = game.moves[-1].score
        # H4 FIRNS
        # 5G V.TEn
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (24, 18),
                   'tiles': {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('n', 75)},
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        game = State.ctx.game
        score2 = game.moves[-1].score

        self.assertEqual(score1, score2, 'same score with _ and e expected')

    def test_remove_blanko(self):
        # H4 FIRNS
        # 5G V.TEn
        #    MÖS
        data = [    {   'button': 'GREEN', 'score': (24, 0),
                        'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), 
                                   (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                    },
                    {   'button': 'RED', 'score': (24, 18),
                        'tiles': {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)},
                    },
                    {   'button': 'GREEN', 'score': (43, 18),
                        'tiles': {(1, 9): Tile('M', 75), (2, 9): Tile('Ö', 75), (3, 9): Tile('S', 75)},
                    },                                   
        ]  # fmt:off
        self.run_data(start_button='red', data=data)
        game = State.ctx.game

        # admin changes
        admin_insert_moves(game, 2, None)
        assert 5 == len(game.moves), 'invalid count of moves'

        remove_blanko(game, '5K', None)
        assert game.moves[-1].score == (43, 9), f'score {game.moves[-1].score} == 43,9'
        self.assertEqual(
            game.moves[-1].board,
            {   (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
                (7, 7): Tile('S', 75),
                (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75),
                (1, 9): Tile('M', 75), (2, 9): Tile('Ö', 75), (3, 9): Tile('S', 75),
            },
            f'invalid board',
        )  # fmt:off

    def test_set_blanko(self):
        # H4 FIRNS
        data = [ { 'button': 'GREEN', 'score': (22, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('_', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        game = State.ctx.game
        # admin changes
        set_blankos(game, 'H5', 'i')
        assert game.moves[-1].board[(4, 7)] == Tile('i', 99), f'invalid board {game.moves[-1].board}'


if __name__ == '__main__':
    unittest.main(module='test_algorithm_blanko')
