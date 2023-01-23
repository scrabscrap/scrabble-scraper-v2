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
import logging.config
import os
import unittest

logging.config.fileConfig(fname=os.path.dirname(os.path.abspath(__file__)) + '/test_log.conf',
                          disable_existing_loggers=False)

from scrabble import Move, MoveType
from state import State
from display import Display
from scrabblewatch import ScrabbleWatch


class AlgorithmTestCase(unittest.TestCase):
    """Test class for algorithm"""

    def setUp(self):
        # logging.disable(logging.DEBUG)  # falls Info-Ausgaben erfolgen sollen
        # logging.disable(logging.ERROR)
        display = Display()
        watch = ScrabbleWatch(display)
        self.state = State(watch=watch)

    def test_10(self):
        """Test 10 - hand on board"""
        from processing import filter_candidates

        # check hand without connection to tiles
        # H4 FIRNS
        board = {(0, 0): ('_', 75), (0, 1): ('_', 75), (0, 2): ('_', 75), (0, 3): ('_', 75),
                 (1, 0): ('_', 75), (1, 1): ('_', 75), (1, 2): ('_', 75), (1, 3): ('_', 75),
                 (2, 0): ('_', 75), (2, 1): ('_', 75), (2, 2): ('_', 75), (2, 3): ('_', 75),
                 (2, 4): ('_', 75), (2, 5): ('_', 75), (2, 6): ('_', 75),
                 (3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('N', 75)}
        result_set: set = filter_candidates((7, 7), set(board.keys()), set())
        expected = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                    (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('N', 75)}
        expected_set: set = set(expected)
        self.assertEqual(result_set, expected_set, 'Test 10: difference in sets')

        # check hand without connection to tiles
        board = {(0, 0): ('_', 75), (0, 1): ('_', 75), (0, 2): ('_', 75), (0, 3): ('_', 75),
                 (1, 0): ('_', 75), (1, 1): ('_', 75), (1, 2): ('_', 75), (1, 3): ('_', 75),
                 (2, 0): ('_', 75), (2, 1): ('_', 75), (2, 2): ('_', 75), (2, 3): ('_', 75),
                 (2, 4): ('_', 75), (2, 5): ('_', 75), (2, 6): ('_', 75), (2, 7): ('_', 75),
                 (3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('N', 75)}
        result_set: set = filter_candidates((7, 7), set(board.keys()), set())
        expected = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                    (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('N', 75)}
        expected_set: set = set(expected)
        self.assertNotEqual(result_set, expected_set, 'Test 10: no difference in sets')

    def test_101(self):
        """Test 101 - Algorithm: empty board with tiles exchange"""

        state = State()
        game = state.game
        game.new_game()

        # empty
        board = {}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=None, is_vertical=False, word='', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(1, len(game.moves), 'invalid count of moves')
        self.assertEqual((0, 0), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_102(self):
        """Test 102 - Algorithm: first move"""

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(1, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 0), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_103(self):
        """Test 103 - Algorithm: crossed move"""

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 5G V.TEN
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('N', 75)}
        new_tiles = {(4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('N', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 6), is_vertical=True, word='V.TEN', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 20), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_104(self):
        """Test 104 - Algorithm: move at top (horizontal)"""

        state = State()
        game = state.game
        game.new_game()

        # H4 TURNeNS
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75)}
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='TURN_NS',
                    new_tiles=board.copy(), removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')
        # 8A SAUNIER.
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75),
                 (7, 0): ('S', 75), (7, 1): ('A', 75), (7, 2): ('U', 75), (7, 3): ('N', 75), (7, 4): ('I', 75),
                 (7, 5): ('E', 75), (7, 6): ('R', 75)}
        new_tiles = {(7, 0): ('S', 75), (7, 1): ('A', 75), (7, 2): ('U', 75), (7, 3): ('N', 75), (7, 4): ('I', 75),
                     (7, 5): ('E', 75), (7, 6): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(7, 0), is_vertical=True, word='SAUNIER', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')
        # A8 .UPER
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75),
                 (7, 0): ('S', 75), (7, 1): ('A', 75), (7, 2): ('U', 75), (7, 3): ('N', 75), (7, 4): ('I', 75),
                 (7, 5): ('E', 75), (7, 6): ('R', 75),
                 (8, 0): ('U', 75), (9, 0): ('P', 75), (10, 0): ('E', 75), (11, 0): ('R', 75)}
        new_tiles = {(8, 0): ('U', 75), (9, 0): ('P', 75), (10, 0): ('E', 75), (11, 0): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(7, 0), is_vertical=False, word='.UPER', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(2, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(3, len(game.moves), 'invalid count of moves')
        self.assertEqual((73, 74), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_105(self):
        """Test 105 - Algorithm: move at top (vertical)"""

        state = State()
        game = state.game
        game.new_game()

        # H4 TURNeNS
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 8A SAUNIER.
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75),
                 (7, 0): ('S', 75), (7, 1): ('A', 75), (7, 2): ('U', 75), (7, 3): ('N', 75), (7, 4): ('I', 75),
                 (7, 5): ('E', 75), (7, 6): ('R', 75)}
        new_tiles = {(7, 0): ('S', 75), (7, 1): ('A', 75), (7, 2): ('U', 75), (7, 3): ('N', 75), (7, 4): ('I', 75),
                     (7, 5): ('E', 75), (7, 6): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(7, 0), is_vertical=True, word='SAUNIER.', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 74), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_106(self):
        """Test 106 - Algorithm: move at bottom (horizontal)"""

        state = State()
        game = state.game
        game.new_game()

        # H2 TURNeNS
        board = {(1, 7): ('T', 75), (2, 7): ('U', 75), (3, 7): ('R', 75), (4, 7): ('N', 75), (5, 7): ('_', 75),
                 (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(1, 7), is_vertical=False, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 8H .AUNIERE
        board = {(1, 7): ('T', 75), (2, 7): ('U', 75), (3, 7): ('R', 75), (4, 7): ('N', 75), (5, 7): ('_', 75),
                 (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (7, 8): ('A', 75), (7, 9): ('U', 75), (7, 10): ('N', 75), (7, 11): ('I', 75),
                 (7, 12): ('E', 75), (7, 13): ('R', 75), (7, 14): ('E', 75)}
        new_tiles = {(7, 8): ('A', 75), (7, 9): ('U', 75), (7, 10): ('N', 75), (7, 11): ('I', 75),
                     (7, 12): ('E', 75), (7, 13): ('R', 75), (7, 14): ('E', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(7, 7), is_vertical=True, word='.AUNIERE', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # O5 SUP.R
        board = {(1, 7): ('T', 75), (2, 7): ('U', 75), (3, 7): ('R', 75), (4, 7): ('N', 75), (5, 7): ('_', 75),
                 (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (7, 8): ('A', 75), (7, 9): ('U', 75), (7, 10): ('N', 75), (7, 11): ('I', 75),
                 (7, 12): ('E', 75), (7, 13): ('R', 75), (7, 14): ('E', 75),
                 (4, 14): ('S', 75), (5, 14): ('U', 75), (6, 14): ('P', 75), (8, 14): ('R', 75)}
        new_tiles = {(4, 14): ('S', 75), (5, 14): ('U', 75), (6, 14): ('P', 75), (8, 14): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(4, 14), is_vertical=False, word='SUP.R', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(2, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(3, len(game.moves), 'invalid count of moves')
        self.assertEqual((72, 77), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_107(self):
        """Test 107 - Algorithm: move at bottom (vertical)"""

        state = State()
        game = state.game
        game.new_game()

        # H2 TURNeNS
        board = {(1, 7): ('T', 75), (2, 7): ('U', 75), (3, 7): ('R', 75), (4, 7): ('N', 75), (5, 7): ('_', 75),
                 (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(1, 7), is_vertical=False, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 8H .AUNIERE
        board = {(1, 7): ('T', 75), (2, 7): ('U', 75), (3, 7): ('R', 75), (4, 7): ('N', 75), (5, 7): ('_', 75),
                 (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (7, 8): ('A', 75), (7, 9): ('U', 75), (7, 10): ('N', 75), (7, 11): ('I', 75),
                 (7, 12): ('E', 75), (7, 13): ('R', 75), (7, 14): ('E', 75)}
        new_tiles = {(7, 8): ('A', 75), (7, 9): ('U', 75), (7, 10): ('N', 75), (7, 11): ('I', 75),
                     (7, 12): ('E', 75), (7, 13): ('R', 75), (7, 14): ('E', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(7, 7), is_vertical=True, word='.AUNIERE', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 77), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_108(self):
        """Test 108 - Algorithm: move at left border (horizontal)"""

        state = State()
        game = state.game
        game.new_game()

        # 8D TURNeNS
        board = {(7, 3): ('T', 75), (7, 4): ('U', 75), (7, 5): ('R', 75), (7, 6): ('N', 75), (7, 7): ('_', 75),
                 (7, 8): ('N', 75), (7, 9): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(7, 3), is_vertical=True, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # H1 SAUNIER.
        board = {(7, 3): ('T', 75), (7, 4): ('U', 75), (7, 5): ('R', 75), (7, 6): ('N', 75), (7, 7): ('_', 75),
                 (7, 8): ('N', 75), (7, 9): ('S', 75),
                 (0, 7): ('S', 75), (1, 7): ('A', 75), (2, 7): ('U', 75), (3, 7): ('N', 75), (4, 7): ('I', 75),
                 (5, 7): ('E', 75), (6, 7): ('R', 75)}
        new_tiles = {(0, 7): ('S', 75), (1, 7): ('A', 75), (2, 7): ('U', 75), (3, 7): ('N', 75), (4, 7): ('I', 75),
                     (5, 7): ('E', 75), (6, 7): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(0, 7), is_vertical=False, word='SAUNIER.', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 74), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_109(self):
        """Test 109 - Algorithm: move at left border (vertical)"""

        state = State()
        game = state.game
        game.new_game()

        # 8D TURNeNS
        board = {(7, 3): ('T', 75), (7, 4): ('U', 75), (7, 5): ('R', 75), (7, 6): ('N', 75), (7, 7): ('_', 75),
                 (7, 8): ('N', 75), (7, 9): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(7, 3), is_vertical=True, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # H1 SAUNIER.
        board = {(7, 3): ('T', 75), (7, 4): ('U', 75), (7, 5): ('R', 75), (7, 6): ('N', 75), (7, 7): ('_', 75),
                 (7, 8): ('N', 75), (7, 9): ('S', 75),
                 (0, 7): ('S', 75), (1, 7): ('A', 75), (2, 7): ('U', 75), (3, 7): ('N', 75), (4, 7): ('I', 75),
                 (5, 7): ('E', 75), (6, 7): ('R', 75)}
        new_tiles = {(0, 7): ('S', 75), (1, 7): ('A', 75), (2, 7): ('U', 75), (3, 7): ('N', 75), (4, 7): ('I', 75),
                     (5, 7): ('E', 75), (6, 7): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(0, 7), is_vertical=False, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 1H .UPER
        board = {(7, 3): ('T', 75), (7, 4): ('U', 75), (7, 5): ('R', 75), (7, 6): ('N', 75), (7, 7): ('_', 75),
                 (7, 8): ('N', 75), (7, 9): ('S', 75),
                 (0, 7): ('S', 75), (1, 7): ('A', 75), (2, 7): ('U', 75), (3, 7): ('N', 75), (4, 7): ('I', 75),
                 (5, 7): ('E', 75), (6, 7): ('R', 75),
                 (0, 8): ('U', 75), (0, 9): ('P', 75), (0, 10): ('E', 75), (0, 11): ('R', 75)
                 }
        new_tiles = {(0, 8): ('U', 75), (0, 9): ('P', 75), (0, 10): ('E', 75), (0, 11): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(0, 7), is_vertical=True, word='.UPER', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(3, len(game.moves), 'invalid count of moves')
        self.assertEqual((73, 74), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_110(self):
        """Test 110 - Algorithm: move at right border (horizontal)"""

        state = State()
        game = state.game
        game.new_game()

        # 8B TURNeNS
        board = {(7, 1): ('T', 75), (7, 2): ('U', 75), (7, 3): ('R', 75), (7, 4): ('N', 75), (7, 5): ('_', 75),
                 (7, 6): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(7, 1), is_vertical=True, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # H8 .AUNIERE
        board = {(7, 1): ('T', 75), (7, 2): ('U', 75), (7, 3): ('R', 75), (7, 4): ('N', 75), (7, 5): ('_', 75),
                 (7, 6): ('N', 75), (7, 7): ('S', 75),
                 (8, 7): ('A', 75), (9, 7): ('U', 75), (10, 7): ('N', 75), (11, 7): ('I', 75),
                 (12, 7): ('E', 75), (13, 7): ('R', 75), (14, 7): ('E', 75)}
        new_tiles = {(8, 7): ('A', 75), (9, 7): ('U', 75), (10, 7): ('N', 75), (11, 7): ('I', 75),
                     (12, 7): ('E', 75), (13, 7): ('R', 75), (14, 7): ('E', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(7, 7), is_vertical=False, word='.AUNIERE', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 77), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_111(self):
        """Test 111 - Algorithm: move at right border (vertical)"""

        state = State()
        game = state.game
        game.new_game()

        # 8B TURNeNS
        board = {(7, 1): ('T', 75), (7, 2): ('U', 75), (7, 3): ('R', 75), (7, 4): ('N', 75), (7, 5): ('_', 75),
                 (7, 6): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(7, 1), is_vertical=True, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # H8 .AUNIERE
        board = {(7, 1): ('T', 75), (7, 2): ('U', 75), (7, 3): ('R', 75), (7, 4): ('N', 75), (7, 5): ('_', 75),
                 (7, 6): ('N', 75), (7, 7): ('S', 75),
                 (8, 7): ('A', 75), (9, 7): ('U', 75), (10, 7): ('N', 75), (11, 7): ('I', 75),
                 (12, 7): ('E', 75), (13, 7): ('R', 75), (14, 7): ('E', 75)}
        new_tiles = {(8, 7): ('A', 75), (9, 7): ('U', 75), (10, 7): ('N', 75), (11, 7): ('I', 75),
                     (12, 7): ('E', 75), (13, 7): ('R', 75), (14, 7): ('E', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(7, 7), is_vertical=False, word='.AUNIERE', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 15E SUP.R
        board = {(7, 1): ('T', 75), (7, 2): ('U', 75), (7, 3): ('R', 75), (7, 4): ('N', 75), (7, 5): ('_', 75),
                 (7, 6): ('N', 75), (7, 7): ('S', 75),
                 (8, 7): ('A', 75), (9, 7): ('U', 75), (10, 7): ('N', 75), (11, 7): ('I', 75),
                 (12, 7): ('E', 75), (13, 7): ('R', 75), (14, 7): ('E', 75),
                 (14, 4): ('S', 75), (14, 5): ('U', 75), (14, 6): ('P', 75), (14, 8): ('R', 75)}
        new_tiles = {(14, 4): ('S', 75), (14, 5): ('U', 75), (14, 6): ('P', 75), (14, 8): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(14, 4), is_vertical=True, word='SUP.R', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(2, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(3, len(game.moves), 'invalid count of moves')
        self.assertEqual((72, 77), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_112(self):
        """Test 112 - Algorithm: challenge without move"""

        state = State()
        game = state.game
        game.new_game()
        try:
            game.add_valid_challenge(player=0, played_time=(1, 0))
        except Exception:
            pass
        else:
            self.fail("Test 112 Exception expected")

    def test_113(self):
        """Test 113 - Algorithm: not enough point for a challenge"""

        state = State()
        game = state.game
        game.new_game()
        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        game.add_invalid_challenge(played_time=(1, 1), player=1)

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, -10), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_114(self):
        """Test 114 - Algorithm: valid challenge"""

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        board = {}
        game.add_valid_challenge(played_time=(1, 1), player=1)

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((0, 0), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_115(self):
        """Test 115 - Algorithm: invalid challenge"""

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 5G V.TEN
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('N', 75)}
        new_tiles = {(4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('N', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 6), is_vertical=True, word='V.TEN', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        game.add_invalid_challenge(played_time=(2, 1), player=0)

        self.assertEqual(3, len(game.moves), 'invalid count of moves')
        self.assertEqual((14, 20), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_116(self):
        """Test 116 - Algorithm: valid callenge - tiles not removed"""
        # currently not supported
        pass

    def test_117(self):
        """Test 117 - Algorithm: extend a word"""

        state = State()
        game = state.game
        game.new_game()

        # H5 TEST
        board = {(4, 7): ('T', 75), (5, 7): ('E', 75), (6, 7): ('S', 75), (7, 7): ('T', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(4, 7), is_vertical=False, word='TEST', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # H5 ....ER
        board = {(4, 7): ('T', 75), (5, 7): ('E', 75), (6, 7): ('S', 75), (7, 7): ('T', 75),
                 (8, 7): ('E', 75), (9, 7): ('R', 75)}
        new_tiles = {(8, 7): ('E', 75), (9, 7): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 7), is_vertical=False, word='....ER', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((8, 6), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_118(self):
        """Test 118 - Algorithm: word between two word"""

        state = State()
        game = state.game
        game.new_game()

        # H5 TEST
        board = {(4, 7): ('T', 75), (5, 7): ('E', 75), (6, 7): ('S', 75), (7, 7): ('T', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(4, 7), is_vertical=False, word='TEST', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 5H .AT
        board = {(4, 7): ('T', 75), (5, 7): ('E', 75), (6, 7): ('S', 75), (7, 7): ('T', 75),
                 (4, 8): ('A', 75), (4, 9): ('T', 75)}
        new_tiles = {(4, 8): ('A', 75), (4, 9): ('T', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 7), is_vertical=True, word='.AT', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 8H .UT
        board = {(4, 7): ('T', 75), (5, 7): ('E', 75), (6, 7): ('S', 75), (7, 7): ('T', 75),
                 (4, 8): ('A', 75), (4, 9): ('T', 75),
                 (7, 8): ('U', 75), (7, 9): ('T', 75)}
        new_tiles = {(7, 8): ('U', 75), (7, 9): ('T', 75)}
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(7, 7), is_vertical=True, word='.UT', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(2, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # J5 .ES.
        board = {(4, 7): ('T', 75), (5, 7): ('E', 75), (6, 7): ('S', 75), (7, 7): ('T', 75),
                 (4, 8): ('A', 75), (4, 9): ('T', 75),
                 (7, 8): ('U', 75), (7, 9): ('T', 75),
                 (5, 9): ('E', 75), (6, 9): ('S', 75)}
        new_tiles = {(5, 9): ('E', 75), (6, 9): ('S', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 9), is_vertical=False, word='.ES.', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(2, 2), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(4, len(game.moves), 'invalid count of moves')
        self.assertEqual((11, 9), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_119(self):
        """Test 119 - Algorithm: calculation double letter"""

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(1, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 0), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_120(self):
        """Test 120 - Algorithm: calculation triple letter"""

        state = State()
        game = state.game
        game.new_game()

        # H4 TURNeNS
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 6B SAUNIE.E
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75),
                 (5, 1): ('S', 75), (5, 2): ('A', 75), (5, 3): ('U', 75), (5, 4): ('N', 75), (5, 5): ('I', 75),
                 (5, 6): ('E', 75), (5, 8): ('E', 75)}
        new_tiles = {(5, 1): ('S', 75), (5, 2): ('A', 75), (5, 3): ('U', 75), (5, 4): ('N', 75), (5, 5): ('I', 75),
                     (5, 6): ('E', 75), (5, 8): ('E', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(5, 1), is_vertical=True, word='SAUNIE.E', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 62), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_121(self):
        """Test 121 - Algorithm: calculation double word"""

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 5G V.TEN
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('N', 75)}
        new_tiles = {(4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('N', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 6), is_vertical=True, word='V.TEN', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 20), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_122(self):
        """Test 122 - Algorithm: calculation triple word"""

        state = State()
        game = state.game
        game.new_game()

        # H4 TURNeNS
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 8A SAUNIER.
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75),
                 (7, 0): ('S', 75), (7, 1): ('A', 75), (7, 2): ('U', 75), (7, 3): ('N', 75), (7, 4): ('I', 75),
                 (7, 5): ('E', 75), (7, 6): ('R', 75)}
        new_tiles = {(7, 0): ('S', 75), (7, 1): ('A', 75), (7, 2): ('U', 75), (7, 3): ('N', 75), (7, 4): ('I', 75),
                     (7, 5): ('E', 75), (7, 6): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(7, 0), is_vertical=True, word='SAUNIER.', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((64, 74), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_123(self):
        """Test 123 - Algorithm: calculation double letter (blank on double letter field)"""

        state = State()
        game = state.game
        game.new_game()

        # H4 fIRNS
        board = {(3, 7): ('_', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='_IRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(1, len(game.moves), 'invalid count of moves')
        self.assertEqual((8, 0), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_124(self):
        """Test 124 - Algorithm: calculation triple letter (blank on double letter field)"""

        state = State()
        game = state.game
        game.new_game()

        # H4 TURNENS
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('E', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='TURNENS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 6B sAUNiE.E
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('E', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75),
                 (5, 1): ('_', 75), (5, 2): ('A', 75), (5, 3): ('U', 75), (5, 4): ('N', 75), (5, 5): ('_', 75),
                 (5, 6): ('E', 75), (5, 8): ('E', 75)}
        new_tiles = {(5, 1): ('_', 75), (5, 2): ('A', 75), (5, 3): ('U', 75), (5, 4): ('N', 75), (5, 5): ('_', 75),
                     (5, 6): ('E', 75), (5, 8): ('E', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(5, 1), is_vertical=True, word='_AUN_E.E', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((66, 56), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_125(self):
        """Test 125 - Algorithm: calculation double word (blank on double letter field)"""

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 5G V.TEn
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('_', 75)}
        new_tiles = {(4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('_', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 6), is_vertical=True, word='V.TE_', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 18), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_126(self):
        """Test 126 - Algorithm: calculation triple word (blank on double letter field)"""

        state = State()
        game = state.game
        game.new_game()

        # H4 TURNeNS
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='TURN_NS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 8A sAUNIER.
        board = {(3, 7): ('T', 75), (4, 7): ('U', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('_', 75),
                 (8, 7): ('N', 75), (9, 7): ('S', 75),
                 (7, 0): ('_', 75), (7, 1): ('A', 75), (7, 2): ('U', 75), (7, 3): ('N', 75), (7, 4): ('I', 75),
                 (7, 5): ('E', 75), (7, 6): ('R', 75)}
        new_tiles = {(7, 0): ('_', 75), (7, 1): ('A', 75), (7, 2): ('U', 75), (7, 3): ('N', 75), (7, 4): ('I', 75),
                     (7, 5): ('E', 75), (7, 6): ('R', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(7, 0), is_vertical=True, word='_AUNIER.', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

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

        state = State()
        game = state.game
        game.new_game()

        # H4 FJRNS
        board = {(3, 7): ('F', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        try:
            move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FJRNS',
                        new_tiles=new_tiles, removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
            game.add_move(move)
        except Exception:
            pass
        else:
            self.fail('Test 129 Exception expected')

    def test_130(self):
        """Test 130 - Algorithm: changed tile with higher propability"""
        from processing import _recalculate_score_on_tiles_change  # type: ignore
        state = State()
        game = state.game
        game.new_game()

        # H4 FJRNS
        board = {(3, 7): ('F', 75), (4, 7): ('J', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FJRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')
        self.assertEqual((34, 0), game.moves[-1].score)

        # 5G V.TEn
        board = {(3, 7): ('F', 75), (4, 7): ('I', 85), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('_', 75)}
        new_tiles = {(4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('_', 75)}

        # simulate changed tiles
        changed = {(4, 7): ('I', 85)}
        _recalculate_score_on_tiles_change(game=game, board=board, changed=changed)
        score = game.moves[-1].score

        # next move
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 6), is_vertical=True, word='V.TE_', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')
        # score changed from 34 to 24
        self.assertEqual((24, 18), game.moves[-1].score)

    def test_131(self):
        """Test 131 - Algorithm: correct letter to blank"""

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FJRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')
        self.assertEqual((24, 0), game.moves[-1].score)

        # TODO: process changed tiles in processing.py
        # i -> blank
        # board = {(3, 7): ('F', 75), (4, 7): ('_', 80), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        # new_tiles = {}
        # move = Move(type=MoveType.regular, player=1, coord=None, is_vertical=False, word='', new_tiles=new_tiles,
        #             removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        # game.add_move(move)
        # score = game.moves[-1].score
        # logging.debug(f'score {score} / moves {len(game.moves)}')

        # self.assertEqual(2, len(game.moves), 'invalid count of moves')
        # self.assertEqual((22, 0), game.moves[-1].score, 'invalid scores')
        # self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_132(self):
        """Test 132 - Algorithm: new tile with lower propability"""

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 85), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')
        self.assertEqual((24, 0), game.moves[-1].score)

        # TODO: process changed tiles in processing.py
        # i -> j
        # board = {(3, 7): ('F', 75), (4, 7): ('J', 80), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        # new_tiles = {}
        # move = Move(type=MoveType.regular, player=1, coord=None, is_vertical=False, word='', new_tiles=new_tiles,
        #             removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        # game.add_move(move)
        # score = game.moves[-1].score
        # logging.debug(f'score {score} / moves {len(game.moves)}')

        # self.assertEqual(2, len(game.moves), 'invalid count of moves')
        # self.assertEqual((22, 0), game.moves[-1].score, 'invalid scores')
        # self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

    def test_141(self):
        """Test 141 - Algorithm: change tile via admin call - first move"""
        from processing import recalculate_score_on_admin_change

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 85), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        prev_score = game.moves[-1].score
        logging.debug(f'score {prev_score} / moves {len(game.moves)}')

        # admin call
        move_number = 1
        col = 7
        row = 7
        recalculate_score_on_admin_change(game, int(move_number), (col, row), False, word='RNS')
        self.assertEqual((6, 0), game.moves[-1].score, 'invalid scores')

    def test_142(self):
        """Test 142 - Algorithm: 2 moves on board correct first move"""
        from processing import recalculate_score_on_admin_change

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'score {score} / moves {len(game.moves)}')

        # 5G V.TEn
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('_', 75)}
        new_tiles = {(4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('_', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 6), is_vertical=True, word='V.TE_', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'before score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 18), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

        # admin call
        move_number = 1
        col = 4
        row = 7
        recalculate_score_on_admin_change(game, int(move_number), (col, row), False, word='IRNS')
        self.assertEqual((8, 18), game.moves[-1].score, 'invalid scores')
        logging.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

    def test_143(self):
        """Test 143 - Algorithm: 2 moves on board correct second move"""
        from processing import recalculate_score_on_admin_change

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score

        # 5G V.TEn
        board = {(3, 7): ('F', 75), (4, 7): ('I', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('_', 75)}
        new_tiles = {(4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('_', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 6), is_vertical=True, word='V.TE_', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'before score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((24, 18), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

        # admin call
        move_number = 2
        col = 4
        row = 7
        recalculate_score_on_admin_change(game, int(move_number), (col, row), True, word='ITEN')
        self.assertEqual((24, 8), game.moves[-1].score, 'invalid scores')
        logging.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

    def test_144(self):
        """Test 144 - Algorithm: 2 moves on board correct first move"""
        from processing import recalculate_score_on_admin_change

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('Ö', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        score = game.moves[-1].score

        # 5G V.TEn
        board = {(3, 7): ('F', 75), (4, 7): ('Ö', 75), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75),
                 (4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('_', 75)}
        new_tiles = {(4, 6): ('V', 75), (4, 8): ('T', 75), (4, 9): ('E', 75), (4, 10): ('_', 75)}
        move = Move(move_type=MoveType.REGULAR, player=1, coord=(4, 6), is_vertical=True, word='V.TE_', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 1), previous_score=score)
        game.add_move(move)
        score = game.moves[-1].score
        logging.debug(f'before score {score} / moves {len(game.moves)}')

        self.assertEqual(2, len(game.moves), 'invalid count of moves')
        self.assertEqual((38, 32), game.moves[-1].score, 'invalid scores')
        self.assertDictEqual(board, game.moves[-1].board, 'invalid board')

        # admin call
        move_number = 1
        col = 3
        row = 7
        recalculate_score_on_admin_change(game, int(move_number), (col, row), False, word='FIRNS')
        self.assertEqual((24, 18), game.moves[-1].score, 'invalid scores')
        logging.debug(f'score {game.moves[-1].score} / moves {len(game.moves)}')

    def test_145(self):
        """Test 145 - Algorithm: change tile to exchange via admin call - first move"""
        from processing import recalculate_score_on_admin_change

        state = State()
        game = state.game
        game.new_game()

        # H4 FIRNS
        board = {(3, 7): ('F', 75), (4, 7): ('I', 85), (5, 7): ('R', 75), (6, 7): ('N', 75), (7, 7): ('S', 75)}
        new_tiles = board.copy()
        move = Move(move_type=MoveType.REGULAR, player=0, coord=(3, 7), is_vertical=False, word='FIRNS', new_tiles=new_tiles,
                    removed_tiles={}, board=board, played_time=(1, 0), previous_score=(0, 0))
        game.add_move(move)
        prev_score = game.moves[-1].score
        logging.debug(f'score {prev_score} / moves {len(game.moves)}')

        # admin call
        move_number = 1
        col = 0
        row = 0
        recalculate_score_on_admin_change(game, int(move_number), (col, row), True, word='')
        self.assertEqual((0, 0), game.moves[-1].score, 'invalid scores')


if __name__ == '__main__':
    unittest.main()
