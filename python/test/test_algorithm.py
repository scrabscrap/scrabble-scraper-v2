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
import sys
import unittest

import numpy as np

from config import config
from display import Display
from move import BoardType, MoveType, NoMoveError, Tile
from processing import (
    _move_processing,
    _recalculate_score_on_tiles_change,  # type: ignore
    admin_change_move,
    admin_insert_moves,
    end_of_game,
    filter_candidates,
    remove_blanko,
    set_blankos,
)
from scrabble import Game
from scrabblewatch import ScrabbleWatch
from state import State

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, force=True, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'
)
logger = logging.getLogger(__name__)


class AlgorithmTestCase(unittest.TestCase):
    """Test class for algorithm"""

    def setUp(self):
        # logger.disable(logger.DEBUG)  # falls Info-Ausgaben erfolgen sollen
        # logger.disable(logger.ERROR)
        ScrabbleWatch.display = Display  # type: ignore
        config.is_testing = True
        return super().setUp()

    def tearDown(self) -> None:
        config.is_testing = False
        return super().tearDown()

    def create_game(self):
        """Erzeugt ein neues Spiel und gibt das Game-Objekt zurück."""
        return State.ctx.game.new_game()

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

        game = self.create_game()
        # empty
        board: BoardType = {}
        with self.assertRaises(NoMoveError):
            game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles={})
        game.add_exchange(player=0, played_time=(1, 0), img=np.zeros((1, 1)))
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')
        self.assert_board_and_score(game, board, (0, 0), 1)

    # def test_132(self):
    #     """Test 132 - Algorithm: new tile with lower propability"""

    #     # H4 FIRNS
    #     new_tiles:BoardType = {
    #         (3, 7): Tile('F', 75), (4, 7): Tile('I', 85), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
    #     }  # fmt:off
    #     board: BoardType = {}
    #     game = self.create_game()
    #     self.add_move(game, board, new_tiles, (0,(1,0)))

    #     self.assert_board_and_score(game, board, (24, 0), 1)

    #     # TODO: process changed tiles in processing.py
    #     # i -> j
    #     # board = {(3, 7): Tile('F', 75), (4, 7): Tile('J', 80), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75)}
    #     # new_tiles = {}
    #     # move = Move(type=MoveType.regular, player=1, coord=None, is_vertical=False, word='', new_tiles=new_tiles,
    #     #             removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
    #     # game.add_move(move)
    #     # score = game.moves[-1].score
    #     # logger.debug(f'score {score} / moves {len(game.moves)}')

    #     # self.assertEqual(2, len(game.moves), 'invalid count of moves')
    #     # self.assertEqual((22, 0), game.moves[-1].score, 'invalid scores')
    #     # self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_150(self):
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 85), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1864, 1984)))

        # time_malus(64sec, 184sec) = (-20, -40)
        score = game.moves[-1].score
        self.assertEqual((24, 0), score, 'score FIRNS')

        end_of_game(game)
        score = game.moves[-1].score
        self.assertEqual((4, -40), score, 'score for overtime expected')


if __name__ == '__main__':
    unittest.main(module='test_algorithm')
