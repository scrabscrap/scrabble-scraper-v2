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
from move import BoardType, MoveType, Tile
from processing import admin_change_move
from scrabble import Game
from scrabblewatch import ScrabbleWatch
from state import State

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, force=True, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'
)
logger = logging.getLogger(__name__)


class AlgorithmAdminTestCase(unittest.TestCase):
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

    def test_141(self):
        """Test 141 - Algorithm: change tile via admin call - first move"""

        # H4 FIRNS
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 85), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # admin call
        admin_change_move(game, 0, MoveType.REGULAR, (5, 7), False, word='RNS')

        self.assert_board_and_score(game, game.moves[-1].board, (6, 0), 1)

    def test_142(self):
        """Test 142 - Algorithm: 2 moves on board correct first move"""

        # H4 FIRNS
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (24, 18), 2)

        # admin call
        admin_change_move(game, 0, MoveType.REGULAR, (4, 7), False, word='IRNS')
        self.assertEqual((8, 18), game.moves[-1].score, 'invalid scores')

    def test_143(self):
        """Test 143 - Algorithm: 2 moves on board correct second move"""

        # H4 FIRNS
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}

        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (24, 18), 2)

        # admin call
        move_number = 1
        col = 4
        row = 7
        admin_change_move(game, move_number, MoveType.REGULAR, (col, row), True, word='ITEN')
        self.assertEqual((24, 8), game.moves[-1].score, 'invalid scores')

    def test_144(self):
        """Test 144 - Algorithm: 2 moves on board correct first move"""

        # H4 FIRNS
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('Ö', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (38, 32), 2)

        # admin call
        move_number = 0
        col = 3
        row = 7
        admin_change_move(game, move_number, MoveType.REGULAR, (col, row), False, word='FIRNS')
        self.assertEqual((24, 18), game.moves[-1].score, 'invalid scores')

    def test_145(self):
        """Test 145 - Algorithm: change tile to exchange via admin call - first move"""

        # H4 FIRNS
        new_tiles: BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 85), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # admin call
        move_number = 0
        admin_change_move(game, int(move_number), MoveType.EXCHANGE)
        self.assertEqual((0, 0), game.moves[-1].score, 'invalid scores')

    def test_146(self):
        """replace blanko with lower character"""

        # H4 TURNeNS
        new_tiles: BoardType = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))
        score1 = game.moves[-1].score

        # H4 TURNeNS
        new_tiles = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('e', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        game.new_game()
        self.add_move(game, board, new_tiles, (0, (1, 1)))
        score = game.moves[-1].score
        self.assertEqual(score1, score, 'same score with _ and e expected')


if __name__ == '__main__':
    unittest.main(module='test_algorithm_admin')
