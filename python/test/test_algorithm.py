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
from scrabble import BoardType, MoveType, NoMoveError, Tile, board_to_string
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
        logger.debug(f'previous board\n{board_to_string(board)}\nnew board\n{board_to_string(new_board)}')
        new_tiles, _, _ = _move_processing(board=new_board, previous_board=board)
        logger.debug(f'result\n{new_tiles=}')
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
        logger.debug(f'previous board\n{board_to_string(board)}\nnew board\n{board_to_string(new_board)}')
        new_tiles, _, _ = _move_processing(board=new_board, previous_board=board)
        logger.debug(f'result\n{new_tiles=}')
        self.assertDictEqual(new_tiles, {(7, 10): Tile('_', 76), (7, 9): Tile('N', 75), (7, 8): Tile('A', 75)}, 'invalid tiles')

        new_board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
            (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75),
            (7, 5): Tile('_', 75), (6, 6): Tile('_', 76), (3, 6): Tile('_', 76), (3, 8): Tile('_', 75),
            (7, 8): Tile('A', 75), (7, 9): Tile('N', 75),
            (7, 11): Tile('_', 76), (7, 10): Tile('_', 76),
        }  # fmt:off
        logger.debug(f'previous board\n{board_to_string(board)}\nnew board\n{board_to_string(new_board)}')
        new_tiles, _, _ = _move_processing(board=new_board, previous_board=board)
        logger.debug(f'result\n{new_tiles=}')
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
        logger.debug(f'previous board\n{board_to_string(board)}\nnew board\n{board_to_string(new_board)}')
        new_tiles, _, _ = _move_processing(board=new_board, previous_board=board)
        logger.debug(f'result\n{new_tiles}')
        self.assertDictEqual(
            new_tiles,
            {(7, 11): Tile('_', 76), (7, 10): Tile('_', 76), (7, 9): Tile('N', 75), (7, 8): Tile('A', 75)},
            'invalid tiles',
        )

    def test_101(self):
        """Test 101 - Algorithm: empty board with tiles exchange"""

        game = State.ctx.game.new_game()

        # empty
        board = {}
        try:
            game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles={})
        except NoMoveError:
            pass
        game.add_exchange(player=0, played_time=(1, 0), img=np.zeros((1, 1)))
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(1, len(game.moves), 'invalid count of moves')
        self.assertEqual((0, 0), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_102(self):
        """Test 102 - Algorithm: first move"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(1, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 0), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_103(self):
        """Test 103 - Algorithm: crossed move"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board: BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')

        # 5G V.TEN
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
            (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75),
        }  # fmt:off
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75)}
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 20), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_104(self):
        """Test 104 - Algorithm: move at top (horizontal)"""

        game = State.ctx.game.new_game()

        # H4 TURNeNS
        board: BoardType = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')
        # 8A SAUNIER.
        new_tiles: BoardType = {
            (7, 0): Tile('S', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
            (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')
        # A8 .UPER
        new_tiles = {(8, 0): Tile('U', 75), (9, 0): Tile('P', 75), (10, 0): Tile('E', 75), (11, 0): Tile('R', 75)}
        board.update(new_tiles)
        game.add_regular(player=0, played_time=(2, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)

        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(3, len(game.moves), 'invalid count of moves')
        self.assertEqual((73, 74), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_105(self):
        """Test 105 - Algorithm: move at top (vertical)"""

        game = State.ctx.game.new_game()

        # H4 TURNeNS
        board: BoardType = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')

        # 8A SAUNIER.
        new_tiles = {
            (7, 0): Tile('S', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
            (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)

        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 74), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_106(self):
        """Test 106 - Algorithm: move at bottom (horizontal)"""

        game = State.ctx.game.new_game()

        # H2 TURNeNS
        board: BoardType = {
            (1, 7): Tile('T', 75), (2, 7): Tile('U', 75), (3, 7): Tile('R', 75), (4, 7): Tile('N', 75),
            (5, 7): Tile('_', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 8H .AUNIERE
        new_tiles = {
            (7, 8): Tile('A', 75), (7, 9): Tile('U', 75), (7, 10): Tile('N', 75), (7, 11): Tile('I', 75),
            (7, 12): Tile('E', 75), (7, 13): Tile('R', 75), (7, 14): Tile('E', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # O5 SUP.R
        new_tiles = {(4, 14): Tile('S', 75), (5, 14): Tile('U', 75), (6, 14): Tile('P', 75), (8, 14): Tile('R', 75)}
        board.update(new_tiles)
        game.add_regular(player=0, played_time=(2, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(3, len(game.moves), 'invalid count of moves')
        self.assertEqual((72, 77), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_107(self):
        """Test 107 - Algorithm: move at bottom (vertical)"""

        game = State.ctx.game
        game.new_game()

        # H2 TURNeNS
        board = {
            (1, 7): Tile('T', 75), (2, 7): Tile('U', 75), (3, 7): Tile('R', 75), (4, 7): Tile('N', 75),
            (5, 7): Tile('_', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')

        # 8H .AUNIERE
        new_tiles = {
            (7, 8): Tile('A', 75), (7, 9): Tile('U', 75), (7, 10): Tile('N', 75), (7, 11): Tile('I', 75),
            (7, 12): Tile('E', 75), (7, 13): Tile('R', 75), (7, 14): Tile('E', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 77), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_108(self):
        """Test 108 - Algorithm: move at left border (horizontal)"""

        game = State.ctx.game
        game.new_game()

        # 8D TURNeNS
        board = {
            (7, 3): Tile('T', 75), (7, 4): Tile('U', 75), (7, 5): Tile('R', 75), (7, 6): Tile('N', 75),
            (7, 7): Tile('_', 75), (7, 8): Tile('N', 75), (7, 9): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')

        # H1 SAUNIER.
        new_tiles = {
            (0, 7): Tile('S', 75), (1, 7): Tile('A', 75), (2, 7): Tile('U', 75), (3, 7): Tile('N', 75),
            (4, 7): Tile('I', 75), (5, 7): Tile('E', 75), (6, 7): Tile('R', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)

        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 74), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_109(self):
        """Test 109 - Algorithm: move at left border (vertical)"""

        game = State.ctx.game.new_game()

        # 8D TURNeNS
        board = {
            (7, 3): Tile('T', 75), (7, 4): Tile('U', 75), (7, 5): Tile('R', 75), (7, 6): Tile('N', 75),
            (7, 7): Tile('_', 75), (7, 8): Tile('N', 75), (7, 9): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # H1 SAUNIER.
        new_tiles = {
            (0, 7): Tile('S', 75), (1, 7): Tile('A', 75), (2, 7): Tile('U', 75), (3, 7): Tile('N', 75),
            (4, 7): Tile('I', 75), (5, 7): Tile('E', 75), (6, 7): Tile('R', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 1H .UPER
        new_tiles = {(0, 8): Tile('U', 75), (0, 9): Tile('P', 75), (0, 10): Tile('E', 75), (0, 11): Tile('R', 75)}
        board.update(new_tiles)
        game.add_regular(player=0, played_time=(2, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(3, len(game.moves), 'invalid count of moves')
        self.assertEqual((73, 74), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_110(self):
        """Test 110 - Algorithm: move at right border (horizontal)"""

        game = State.ctx.game
        game.new_game()

        # 8B TURNeNS
        board = {
            (7, 1): Tile('T', 75), (7, 2): Tile('U', 75), (7, 3): Tile('R', 75), (7, 4): Tile('N', 75),
            (7, 5): Tile('_', 75), (7, 6): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')

        # H8 .AUNIERE
        new_tiles = {
            (8, 7): Tile('A', 75), (9, 7): Tile('U', 75), (10, 7): Tile('N', 75), (11, 7): Tile('I', 75),
            (12, 7): Tile('E', 75), (13, 7): Tile('R', 75), (14, 7): Tile('E', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 77), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_111(self):
        """Test 111 - Algorithm: move at right border (vertical)"""

        game = State.ctx.game.new_game()

        # 8B TURNeNS
        board = {
            (7, 1): Tile('T', 75), (7, 2): Tile('U', 75), (7, 3): Tile('R', 75), (7, 4): Tile('N', 75),
            (7, 5): Tile('_', 75), (7, 6): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # H8 .AUNIERE
        new_tiles = {
            (8, 7): Tile('A', 75), (9, 7): Tile('U', 75), (10, 7): Tile('N', 75), (11, 7): Tile('I', 75),
            (12, 7): Tile('E', 75), (13, 7): Tile('R', 75), (14, 7): Tile('E', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 15E SUP.R
        new_tiles = {(14, 4): Tile('S', 75), (14, 5): Tile('U', 75), (14, 6): Tile('P', 75), (14, 8): Tile('R', 75)}
        board.update(new_tiles)
        game.add_regular(player=0, played_time=(2, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(3, len(game.moves), 'invalid count of moves')
        self.assertEqual((72, 77), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_112(self):
        """Test 112 - Algorithm: challenge without move"""

        game = State.ctx.game.new_game()
        try:
            game.add_challenge_for()
        except IndexError:
            pass
        else:
            self.fail('Test 112 Exception ValueError expected')

    def test_113(self):
        """Test 113 - Algorithm: not enough point for a challenge"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        game.add_challenge_for()

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, -10), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_114(self):
        """Test 114 - Algorithm: valid challenge"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        board = {}
        game.add_withdraw_for(index=-1, img=np.zeros((1, 1)))

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((0, 0), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_115(self):
        """Test 115 - Algorithm: invalid challenge"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 5G V.TEN
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        game.add_challenge_for()

        self.assertEqual(3, len(game.moves), 'invalid count of moves')
        self.assertEqual((14, 20), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_116(self):
        """Test 116 - Algorithm: valid callenge - tiles not removed"""
        # currently not supported
        pass

    def test_117(self):
        """Test 117 - Algorithm: extend a word"""

        game = State.ctx.game.new_game()

        # H5 TEST
        board = {(4, 7): Tile('T', 75), (5, 7): Tile('E', 75), (6, 7): Tile('S', 75), (7, 7): Tile('T', 75)}
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')

        # H5 ....ER
        new_tiles = {(8, 7): Tile('E', 75), (9, 7): Tile('R', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((8, 6), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_118(self):
        """Test 118 - Algorithm: word between two word"""

        game = State.ctx.game.new_game()

        # H5 TEST
        board = {(4, 7): Tile('T', 75), (5, 7): Tile('E', 75), (6, 7): Tile('S', 75), (7, 7): Tile('T', 75)}
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 5H .AT
        new_tiles = {(4, 8): Tile('A', 75), (4, 9): Tile('T', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 8H .UT
        new_tiles = {(7, 8): Tile('U', 75), (7, 9): Tile('T', 75)}
        board.update(new_tiles)
        game.add_regular(player=0, played_time=(2, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # J5 .ES.
        new_tiles = {(5, 9): Tile('E', 75), (6, 9): Tile('S', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(2, 2), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(4, len(game.moves), 'invalid count of moves')
        self.assertEqual((11, 9), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_119(self):
        """Test 119 - Algorithm: calculation double letter"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(1, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 0), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_120(self):
        """Test 120 - Algorithm: calculation triple letter"""

        game = State.ctx.game.new_game()

        # H4 TURNeNS
        board = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75),(9, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 6B SAUNIE.E
        new_tiles = {
            (5, 1): Tile('S', 75), (5, 2): Tile('A', 75), (5, 3): Tile('U', 75), (5, 4): Tile('N', 75),
            (5, 5): Tile('I', 75), (5, 6): Tile('E', 75), (5, 8): Tile('E', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 62), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_121(self):
        """Test 121 - Algorithm: calculation double word"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 5G V.TEN
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 20), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_122(self):
        """Test 122 - Algorithm: calculation triple word"""

        game = State.ctx.game.new_game()

        # H4 TURNeNS
        board = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 8A SAUNIER.
        new_tiles = {
            (7, 0): Tile('S', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
            (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 74), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_123(self):
        """Test 123 - Algorithm: calculation double letter (blank on double letter field)"""

        game = State.ctx.game.new_game()

        # H4 fIRNS
        board = {
            (3, 7): Tile('_', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(1, len(game.moves), 'invalid count of moves')
        self.assertEqual((8, 0), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_124(self):
        """Test 124 - Algorithm: calculation triple letter (blank on double letter field)"""

        game = State.ctx.game.new_game()

        # H4 TURNENS
        board = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('E', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 6B sAUNiE.E
        new_tiles = {
            (5, 1): Tile('_', 75), (5, 2): Tile('A', 75), (5, 3): Tile('U', 75), (5, 4): Tile('N', 75),
            (5, 5): Tile('_', 75), (5, 6): Tile('E', 75), (5, 8): Tile('E', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((66, 56), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_125(self):
        """Test 125 - Algorithm: calculation double word (blank on double letter field)"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 18), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_126(self):
        """Test 126 - Algorithm: calculation triple word (blank on double letter field)"""

        game = State.ctx.game.new_game()

        # H4 TURNeNS
        board = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 8A sAUNIER.
        new_tiles = {
            (7, 0): Tile('_', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
            (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75),
        }  # fmt:off
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 71), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_127(self):
        """Test 127 - Algorithm: tile removed without challenge"""
        pass

    def test_128(self):
        """Test 128 - Algorithm: tile removed without challenge and put again to board"""
        pass

    def test_129(self):
        """Test 129 - Algorithm: space between new tiles"""

        game = State.ctx.game.new_game()

        # H4 F RNS
        board: BoardType = {(3, 7): Tile('F', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75)}
        try:
            game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        except ValueError:
            pass
        else:
            self.fail('Test 129 Exception ValueError expected')

    def test_130(self):
        """Test 130 - Algorithm: changed tile with higher propability"""

        game = State.ctx.game.new_game()

        # H4 FJRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('J', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        new_tiles = board.copy()
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')
        self.assertEqual((34, 0), game.moves[-1].score)

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        board.update(new_tiles)
        # simulate changed tiles
        changed = {(4, 7): Tile('I', 85)}
        _recalculate_score_on_tiles_change(game=game, changed=changed)

        # next move
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')
        # score changed from 34 to 24
        self.assertEqual((24, 18), game.moves[-1].score)

    def test_131(self):
        """Test 131 - Algorithm: correct letter to blank"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')
        self.assertEqual((24, 0), game.moves[-1].score)

        # TODO: process changed tiles in processing.py
        # i -> blank
        # board = {(3, 7): Tile('F', 75), (4, 7): Tile('_', 80), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75)}
        # new_tiles = {}
        # move = Move(type=MoveType.regular, player=1, coord=None, is_vertical=False, word='', new_tiles=new_tiles,
        #             removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        # game.add_move(move)
        # score = game.moves[-1].score
        # logger.debug(f'score {score} / moves {len(game.moves)}')

        # self.assertEqual(2, len(game.moves), 'invalid count of moves')
        # self.assertEqual((22, 0), game.moves[-1].score, 'invalid scores')
        # self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_132(self):
        """Test 132 - Algorithm: new tile with lower propability"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 85), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score
        logger.debug(f'score {score} / moves {len(game.moves)}')
        self.assertEqual((24, 0), game.moves[-1].score)

        # TODO: process changed tiles in processing.py
        # i -> j
        # board = {(3, 7): Tile('F', 75), (4, 7): Tile('J', 80), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75)}
        # new_tiles = {}
        # move = Move(type=MoveType.regular, player=1, coord=None, is_vertical=False, word='', new_tiles=new_tiles,
        #             removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        # game.add_move(move)
        # score = game.moves[-1].score
        # logger.debug(f'score {score} / moves {len(game.moves)}')

        # self.assertEqual(2, len(game.moves), 'invalid count of moves')
        # self.assertEqual((22, 0), game.moves[-1].score, 'invalid scores')
        # self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_141(self):
        """Test 141 - Algorithm: change tile via admin call - first move"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 85), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        prev_score = game.moves[-1].score
        logger.debug(f'score {prev_score} / moves {len(game.moves)}')

        # admin call
        move_number = 0
        col = 5
        row = 7
        admin_change_move(game, move_number, MoveType.REGULAR, (col, row), False, word='RNS')
        self.assertEqual((6, 0), game.moves[-1].score, 'invalid scores')

    def test_142(self):
        """Test 142 - Algorithm: 2 moves on board correct first move"""

        game = State.ctx.game
        game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'before score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 18), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

        # admin call
        move_number = 0
        col = 4
        row = 7
        admin_change_move(game, move_number, MoveType.REGULAR, (col, row), False, word='IRNS')
        self.assertEqual((8, 18), game.moves[-1].score, 'invalid scores')
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

    def test_143(self):
        """Test 143 - Algorithm: 2 moves on board correct second move"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'before score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 18), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

        # admin call
        move_number = 1
        col = 4
        row = 7
        admin_change_move(game, move_number, MoveType.REGULAR, (col, row), True, word='ITEN')
        self.assertEqual((24, 8), game.moves[-1].score, 'invalid scores')
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

    def test_144(self):
        """Test 144 - Algorithm: 2 moves on board correct first move"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('Ö', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        logger.debug(f'before score {game.moves[-1].score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((38, 32), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

        # admin call
        move_number = 0
        col = 3
        row = 7
        admin_change_move(game, move_number, MoveType.REGULAR, (col, row), False, word='FIRNS')
        self.assertEqual((24, 18), game.moves[-1].score, 'invalid scores')
        logger.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

    def test_145(self):
        """Test 145 - Algorithm: change tile to exchange via admin call - first move"""

        game = State.ctx.game.new_game()

        # H4 FIRNS
        board: BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 85), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        prev_score = game.moves[-1].score
        logger.debug(f'score {prev_score} / moves {len(game.moves)}')

        # admin call
        move_number = 0
        admin_change_move(game, int(move_number), MoveType.EXCHANGE)
        self.assertEqual((0, 0), game.moves[-1].score, 'invalid scores')

    def test_146(self):
        """replace blanko with lower character"""
        game = State.ctx.game
        game.new_game()

        # H4 TURNeNS
        board: BoardType = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score1 = game.moves[-1].score
        game.new_game()

        # H4 TURNeNS
        board = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('e', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score
        self.assertEqual(score1, score, 'same score with _ and e expected')

    def test_147(self):
        """replace blanko with lower character"""
        game = State.ctx.game

        game.new_game()
        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('Ö', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score1 = game.moves[-1].score

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        score1 = game.moves[-1].score

        game.new_game()
        # H4 FIRNS
        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('Ö', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        score = game.moves[-1].score

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('e', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)
        score = game.moves[-1].score
        self.assertEqual(score1, score, 'same score with _ and e expected')

    def test_150(self):
        game = State.ctx.game.new_game()

        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 85), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1864, 1984), img=np.zeros((1, 1)), new_tiles=board)
        # time_malus(64sec, 184sec) = (-20, -40)
        score = game.moves[-1].score
        self.assertEqual((24, 0), score, 'score FIRNS')

        end_of_game(game)
        score = game.moves[-1].score
        self.assertEqual((4, -40), score, 'score for overtime expected')

    def test_remove_blanko(self):
        game = State.ctx.game.new_game()

        board = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        board.update(new_tiles)
        game.add_regular(player=1, played_time=(1, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)

        # J2 MÖS.
        new_tiles = {(1, 9): Tile('M', 75), (2, 9): Tile('Ö', 75), (3, 9): Tile('S', 75)}
        board.update(new_tiles)
        game.add_regular(player=0, played_time=(2, 1), img=np.zeros((1, 1)), new_tiles=new_tiles)

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
        game = State.ctx.game.new_game()

        board: BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('_', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=board)
        set_blankos(game, 'H5', 'i')
        assert game.moves[-1].board[(4, 7)] == Tile('i', 99), f'invalid board {game.moves[-1].board}'


if __name__ == '__main__':
    unittest.main(module='test_algorithm')
