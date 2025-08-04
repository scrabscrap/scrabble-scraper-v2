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

import logging
import unittest

import numpy as np

from move import BoardType, NoMoveError, Tile
from processing import end_of_game, filter_candidates
from scrabble import Game
from state import State
from test.test_base import BaseTestClass


class AlgorithmTestCase(BaseTestClass):
    """Test class for algorithm"""

    def add_move(
        self, game: Game, board: BoardType, new_tiles: BoardType, player_info: tuple[int, tuple[int, int]] = ((0, (1, 0)))
    ) -> BoardType:
        """Fügt dem Spiel einen Zug hinzu und gibt das aktualisierte Board zurück."""
        board.update(new_tiles)
        game.add_regular(player=player_info[0], played_time=player_info[1], img=np.zeros((1, 1)), new_tiles=new_tiles)
        # logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')
        return game.moves[-1].board

    def assert_board_and_score(self, game: Game, expected_board: BoardType, expected_score: tuple[int, int], expected_len: int):
        """Hilfsmethode für häufige Assertions."""
        self.assertEqual(expected_len, len(game.moves), 'invalid count of moves')
        self.assertDictEqual(game.moves[-1].board, expected_board, 'invalid board')
        self.assertEqual(game.moves[-1].score, expected_score, 'invalid scores')

    def test_10(self):
        """Test 10 - hand on board"""

        # check hand without connection to tiles
        # H4 FIRNS
        board = {
            (0, 0): Tile('_', 75), (0, 1): Tile('_', 75), (0, 2): Tile('_', 75), (0, 3): Tile('_', 75),
            (1, 0): Tile('_', 75), (1, 1): Tile('_', 75), (1, 2): Tile('_', 75), (1, 3): Tile('_', 75),
            (2, 0): Tile('_', 75), (2, 1): Tile('_', 75), (2, 2): Tile('_', 75), (2, 3): Tile('_', 75),
            (2, 4): Tile('_', 75), (2, 5): Tile('_', 75), (2, 6): Tile('_', 75),
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
            (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75),
        }  # fmt: off
        result_set: set = filter_candidates((7, 7), set(board.keys()), set())
        expected = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
            (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75),
        }  # fmt:off
        expected_set: set = set(expected)
        self.assertEqual(result_set, expected_set, 'Test 10: difference in sets')

        # check hand without connection to tiles
        board = {
            (0, 0): Tile('_', 75), (0, 1): Tile('_', 75), (0, 2): Tile('_', 75), (0, 3): Tile('_', 75),
            (1, 0): Tile('_', 75), (1, 1): Tile('_', 75), (1, 2): Tile('_', 75), (1, 3): Tile('_', 75),
            (2, 0): Tile('_', 75), (2, 1): Tile('_', 75), (2, 2): Tile('_', 75), (2, 3): Tile('_', 75),
            (2, 4): Tile('_', 75), (2, 5): Tile('_', 75), (2, 6): Tile('_', 75), (2, 7): Tile('_', 75),
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
            (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75),
        }  # fmt:off
        result_set: set = filter_candidates((7, 7), set(board.keys()), set())
        expected = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
            (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75),
        }  # fmt:off
        expected_set: set = set(expected)
        self.assertNotEqual(result_set, expected_set, 'Test 10: no difference in sets')

    def test_101(self):
        """Test 101 - Algorithm: empty board with tiles exchange"""

        game = State.ctx.game.new_game()
        # empty
        board: BoardType = {}
        with self.assertRaises(NoMoveError):
            game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles={})
        game.add_exchange(player=0, played_time=(1, 0), img=np.zeros((1, 1)))
        logging.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')
        self.assert_board_and_score(game, board, (0, 0), 1)

    def test_132(self):
        """Test 132 - Algorithm: new tile with lower propability"""
        # H4 FIRNS
        # 5G V.TEN -> VÄTEN (niedrige Prio)
        # data = [ { 'button': 'GREEN', 'score': (24, 0),
        #            'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 80), (5, 7): Tile('R', 75),
        #                       (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
        #          },
        #          { 'button': 'RED', 'score': (24, 20),
        #            'tiles': {(4, 7): Tile('Ä', 75), (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75)},
        #          }
        #         ]  # fmt:off
        # self.run_data(start_button='red', data=data)
        # self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_150(self):
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 85), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = State.ctx.game.new_game()
        self.add_move(game, board, new_tiles, (0, (1864, 1984)))

        # time_malus(64sec, 184sec) = (-20, -40)
        score = game.moves[-1].score
        self.assertEqual((24, 0), score, 'score FIRNS')

        end_of_game(game)
        score = game.moves[-1].score
        self.assertEqual((4, -40), score, 'score for overtime expected')


if __name__ == '__main__':
    unittest.main(module='test_algorithm')
