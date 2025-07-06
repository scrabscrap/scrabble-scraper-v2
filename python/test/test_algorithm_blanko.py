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


class AlgorithmBlankoTestCase(unittest.TestCase):
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

    def test_11(self):
        """Test 11 - Algorithm: remove invalid blanks"""

        game = self.create_game()

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

    # def test_131(self):
    #     """Test 131 - Algorithm: correct letter to blank"""

    #     # H4 FIRNS
    #     new_tiles:BoardType = {
    #         (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
    #     }  # fmt:off
    #     board: BoardType = {}
    #     game = self.create_game()
    #     self.add_move(game, board, new_tiles, (0,(1,0)))

    #     self.assert_board_and_score(game, board, (24, 0), 1)

    #     # TODO: process changed tiles in processing.py
    #     # i -> blank
    #     # board = {(3, 7): Tile('F', 75), (4, 7): Tile('_', 80), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75)}
    #     # new_tiles = {}
    #     # move = Move(type=MoveType.regular, player=1, coord=None, is_vertical=False, word='', new_tiles=new_tiles,
    #     #             removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
    #     # game.add_move(move)
    #     # score = game.moves[-1].score
    #     # logger.debug(f'score {score} / moves {len(game.moves)}')

    #     # self.assertEqual(2, len(game.moves), 'invalid count of moves')
    #     # self.assertEqual((22, 0), game.moves[-1].score, 'invalid scores')
    #     # self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_147(self):
        """replace blanko with lower character"""

        # H4 FIRNS
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('Ö', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))
        score1 = game.moves[-1].score

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        self.add_move(game, board, new_tiles, (1, (1, 1)))
        score1 = game.moves[-1].score

        # H4 FIRNS
        new_tiles = {
            (3, 7): Tile('F', 75), (4, 7): Tile('Ö', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game.new_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('e', 75)}
        self.add_move(game, board, new_tiles, (1, (1, 1)))
        score = game.moves[-1].score
        self.assertEqual(score1, score, 'same score with _ and e expected')

    def test_remove_blanko(self):
        game = self.create_game()

        board = {}
        new_tiles = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        # J2 MÖS.
        new_tiles = {(1, 9): Tile('M', 75), (2, 9): Tile('Ö', 75), (3, 9): Tile('S', 75)}
        self.add_move(game, board, new_tiles, (0, (2, 1)))

        admin_insert_moves(game, 2, None)
        assert 5 == len(game.moves), 'invalid count of moves'

        remove_blanko(game, '5K', None)

        assert game.moves[-1].score == (43, 9), f'score {game.moves[-1].score} == 43,9'
        self.assertEqual(
            game.moves[-1].board,
            {
                (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
                (7, 7): Tile('S', 75),
                (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75),
                (1, 9): Tile('M', 75), (2, 9): Tile('Ö', 75), (3, 9): Tile('S', 75),
            },
            f'invalid board',
        )  # fmt:off

    def test_set_blanko(self):
        new_tiles: BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('_', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))
        set_blankos(game, 'H5', 'i')
        assert game.moves[-1].board[(4, 7)] == Tile('i', 99), f'invalid board {game.moves[-1].board}'


if __name__ == '__main__':
    unittest.main(module='test_algorithm_blanko')
