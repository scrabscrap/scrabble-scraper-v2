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
from move import BoardType, Tile
from processing import _recalculate_score_on_tiles_change  # type: ignore,
from scrabble import Game
from scrabblewatch import ScrabbleWatch
from state import State

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, force=True, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'
)
logger = logging.getLogger(__name__)


class AlgorithmMovesTestCase(unittest.TestCase):
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

    def test_102(self):
        """Test 102 - Algorithm: first move"""

        # H4 FIRNS
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, ((0, (1, 0))))
        self.assert_board_and_score(game, board, (24, 0), 1)

    def test_103(self):
        """Test 103 - Algorithm: crossed move"""

        # H4 FIRNS
        new_tiles: BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, ((0, (1, 0))))

        # 5G V.TEN
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75)}
        self.add_move(game, board, new_tiles, ((1, (1, 1))))
        self.assert_board_and_score(game, board, (24, 20), 2)

    def test_104(self):
        """Test 104 - Algorithm: move at top (horizontal)"""

        # H4 TURNeNS
        new_tiles: BoardType = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, ((0, (1, 0))))

        # 8A SAUNIER.
        new_tiles: BoardType = {
            (7, 0): Tile('S', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
            (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, ((1, (1, 1))))

        # A8 .UPER
        new_tiles = {(8, 0): Tile('U', 75), (9, 0): Tile('P', 75), (10, 0): Tile('E', 75), (11, 0): Tile('R', 75)}
        self.add_move(game, board, new_tiles, ((0, (2, 1))))

        self.assert_board_and_score(game, board, (73, 74), 3)

    def test_105(self):
        """Test 105 - Algorithm: move at top (vertical)"""

        # H4 TURNeNS
        new_tiles: BoardType = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, ((0, (1, 0))))

        # 8A SAUNIER.
        new_tiles = {
            (7, 0): Tile('S', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
            (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, ((1, (1, 1))))

        self.assert_board_and_score(game, board, (64, 74), 2)

    def test_106(self):
        """Test 106 - Algorithm: move at bottom (horizontal)"""

        # H2 TURNeNS
        new_tiles: BoardType = {
            (1, 7): Tile('T', 75), (2, 7): Tile('U', 75), (3, 7): Tile('R', 75), (4, 7): Tile('N', 75),
            (5, 7): Tile('_', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, ((0, (1, 0))))

        # 8H .AUNIERE
        new_tiles = {
            (7, 8): Tile('A', 75), (7, 9): Tile('U', 75), (7, 10): Tile('N', 75), (7, 11): Tile('I', 75),
            (7, 12): Tile('E', 75), (7, 13): Tile('R', 75), (7, 14): Tile('E', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, ((1, (1, 1))))

        # O5 SUP.R
        new_tiles = {(4, 14): Tile('S', 75), (5, 14): Tile('U', 75), (6, 14): Tile('P', 75), (8, 14): Tile('R', 75)}
        self.add_move(game, board, new_tiles, ((0, (2, 1))))

        self.assert_board_and_score(game, board, (72, 77), 3)

    def test_107(self):
        """Test 107 - Algorithm: move at bottom (vertical)"""

        # H2 TURNeNS
        new_tiles:BoardType = {
            (1, 7): Tile('T', 75), (2, 7): Tile('U', 75), (3, 7): Tile('R', 75), (4, 7): Tile('N', 75),
            (5, 7): Tile('_', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 8H .AUNIERE
        new_tiles = {
            (7, 8): Tile('A', 75), (7, 9): Tile('U', 75), (7, 10): Tile('N', 75), (7, 11): Tile('I', 75),
            (7, 12): Tile('E', 75), (7, 13): Tile('R', 75), (7, 14): Tile('E', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (64, 77), 2)

    def test_108(self):
        """Test 108 - Algorithm: move at left border (horizontal)"""

        # 8D TURNeNS
        new_tiles:BoardType = {
            (7, 3): Tile('T', 75), (7, 4): Tile('U', 75), (7, 5): Tile('R', 75), (7, 6): Tile('N', 75),
            (7, 7): Tile('_', 75), (7, 8): Tile('N', 75), (7, 9): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # H1 SAUNIER.
        new_tiles = {
            (0, 7): Tile('S', 75), (1, 7): Tile('A', 75), (2, 7): Tile('U', 75), (3, 7): Tile('N', 75),
            (4, 7): Tile('I', 75), (5, 7): Tile('E', 75), (6, 7): Tile('R', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (64, 74), 2)

    def test_109(self):
        """Test 109 - Algorithm: move at left border (vertical)"""

        # 8D TURNeNS
        new_tiles:BoardType = {
            (7, 3): Tile('T', 75), (7, 4): Tile('U', 75), (7, 5): Tile('R', 75), (7, 6): Tile('N', 75),
            (7, 7): Tile('_', 75), (7, 8): Tile('N', 75), (7, 9): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # H1 SAUNIER.
        new_tiles = {
            (0, 7): Tile('S', 75), (1, 7): Tile('A', 75), (2, 7): Tile('U', 75), (3, 7): Tile('N', 75),
            (4, 7): Tile('I', 75), (5, 7): Tile('E', 75), (6, 7): Tile('R', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        # 1H .UPER
        new_tiles = {(0, 8): Tile('U', 75), (0, 9): Tile('P', 75), (0, 10): Tile('E', 75), (0, 11): Tile('R', 75)}
        self.add_move(game, board, new_tiles, (0, (2, 1)))

        self.assert_board_and_score(game, board, (73, 74), 3)

    def test_110(self):
        """Test 110 - Algorithm: move at right border (horizontal)"""

        # 8B TURNeNS
        new_tiles:BoardType = {
            (7, 1): Tile('T', 75), (7, 2): Tile('U', 75), (7, 3): Tile('R', 75), (7, 4): Tile('N', 75),
            (7, 5): Tile('_', 75), (7, 6): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # H8 .AUNIERE
        new_tiles = {
            (8, 7): Tile('A', 75), (9, 7): Tile('U', 75), (10, 7): Tile('N', 75), (11, 7): Tile('I', 75),
            (12, 7): Tile('E', 75), (13, 7): Tile('R', 75), (14, 7): Tile('E', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (64, 77), 2)

    def test_111(self):
        """Test 111 - Algorithm: move at right border (vertical)"""

        # 8B TURNeNS
        new_tiles:BoardType = {
            (7, 1): Tile('T', 75), (7, 2): Tile('U', 75), (7, 3): Tile('R', 75), (7, 4): Tile('N', 75),
            (7, 5): Tile('_', 75), (7, 6): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # H8 .AUNIERE
        new_tiles = {
            (8, 7): Tile('A', 75), (9, 7): Tile('U', 75), (10, 7): Tile('N', 75), (11, 7): Tile('I', 75),
            (12, 7): Tile('E', 75), (13, 7): Tile('R', 75), (14, 7): Tile('E', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        # 15E SUP.R
        new_tiles = {(14, 4): Tile('S', 75), (14, 5): Tile('U', 75), (14, 6): Tile('P', 75), (14, 8): Tile('R', 75)}
        self.add_move(game, board, new_tiles, (0, (2, 1)))

        self.assert_board_and_score(game, board, (72, 77), 3)

    def test_112(self):
        """Test 112 - Algorithm: challenge without move"""

        game = self.create_game()
        with self.assertRaises(IndexError):
            game.add_challenge_for()

    def test_113(self):
        """Test 113 - Algorithm: not enough point for a challenge"""

        # H4 FIRNS
        new_tiles: BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))
        game.add_challenge_for()

        self.assert_board_and_score(game, board, (24, -10), 2)

    def test_114(self):
        """Test 114 - Algorithm: valid challenge"""

        # H4 FIRNS
        new_tiles: BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        board = {}
        game.add_withdraw_for(index=-1, img=np.zeros((1, 1)))

        self.assert_board_and_score(game, board, (0, 0), 2)

    def test_115(self):
        """Test 115 - Algorithm: invalid challenge"""

        # H4 FIRNS
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 5G V.TEN
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75)}
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        game.add_challenge_for()

        self.assert_board_and_score(game, board, (14, 20), 3)

    def test_116(self):
        """Test 116 - Algorithm: valid callenge - tiles not removed"""
        # currently not supported
        pass

    def test_117(self):
        """Test 117 - Algorithm: extend a word"""

        # H5 TEST
        new_tiles: BoardType = {(4, 7): Tile('T', 75), (5, 7): Tile('E', 75), (6, 7): Tile('S', 75), (7, 7): Tile('T', 75)}
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # H5 ....ER
        new_tiles = {(8, 7): Tile('E', 75), (9, 7): Tile('R', 75)}
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (8, 6), 2)

    def test_118(self):
        """Test 118 - Algorithm: word between two word"""

        # H5 TEST
        new_tiles: BoardType = {(4, 7): Tile('T', 75), (5, 7): Tile('E', 75), (6, 7): Tile('S', 75), (7, 7): Tile('T', 75)}
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 5H .AT
        new_tiles = {(4, 8): Tile('A', 75), (4, 9): Tile('T', 75)}
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        # 8H .UT
        new_tiles = {(7, 8): Tile('U', 75), (7, 9): Tile('T', 75)}
        self.add_move(game, board, new_tiles, (0, (2, 1)))

        # J5 .ES.
        new_tiles = {(5, 9): Tile('E', 75), (6, 9): Tile('S', 75)}
        self.add_move(game, board, new_tiles, (1, (2, 2)))

        self.assert_board_and_score(game, board, (11, 9), 4)

    def test_119(self):
        """Test 119 - Algorithm: calculation double letter"""

        # H4 FIRNS
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        self.assert_board_and_score(game, board, (24, 0), 1)

    def test_120(self):
        """Test 120 - Algorithm: calculation triple letter"""

        # H4 TURNeNS
        new_tiles:BoardType = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75),(9, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 6B SAUNIE.E
        new_tiles = {
            (5, 1): Tile('S', 75), (5, 2): Tile('A', 75), (5, 3): Tile('U', 75), (5, 4): Tile('N', 75),
            (5, 5): Tile('I', 75), (5, 6): Tile('E', 75), (5, 8): Tile('E', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (64, 62), 2)

    def test_121(self):
        """Test 121 - Algorithm: calculation double word"""

        # H4 FIRNS
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 5G V.TEN
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75)}
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (24, 20), 2)

    def test_122(self):
        """Test 122 - Algorithm: calculation triple word"""

        # H4 TURNeNS
        new_tiles:BoardType = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 8A SAUNIER.
        new_tiles = {
            (7, 0): Tile('S', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
            (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (64, 74), 2)

    def test_123(self):
        """Test 123 - Algorithm: calculation double letter (blank on double letter field)"""

        # H4 fIRNS
        new_tiles:BoardType = {
            (3, 7): Tile('_', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        self.assert_board_and_score(game, board, (8, 0), 1)

    def test_124(self):
        """Test 124 - Algorithm: calculation triple letter (blank on double letter field)"""

        # H4 TURNENS
        new_tiles:BoardType = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('E', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 6B sAUNiE.E
        new_tiles = {
            (5, 1): Tile('_', 75), (5, 2): Tile('A', 75), (5, 3): Tile('U', 75), (5, 4): Tile('N', 75),
            (5, 5): Tile('_', 75), (5, 6): Tile('E', 75), (5, 8): Tile('E', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (66, 56), 2)

    def test_125(self):
        """Test 125 - Algorithm: calculation double word (blank on double letter field)"""

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

    def test_126(self):
        """Test 126 - Algorithm: calculation triple word (blank on double letter field)"""

        # H4 TURNeNS
        new_tiles:BoardType = {
            (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
            (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 8A sAUNIER.
        new_tiles = {
            (7, 0): Tile('_', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
            (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75),
        }  # fmt:off
        self.add_move(game, board, new_tiles, (1, (1, 1)))

        self.assert_board_and_score(game, board, (64, 71), 2)

    # def test_127(self):
    #     """Test 127 - Algorithm: tile removed without challenge"""
    #     pass

    # def test_128(self):
    #     """Test 128 - Algorithm: tile removed without challenge and put again to board"""
    #     pass

    def test_129(self):
        """Test 129 - Algorithm: space between new tiles"""

        # H4 F RNS
        new_tiles: BoardType = {(3, 7): Tile('F', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75)}
        game = self.create_game()
        with self.assertRaises(ValueError):
            game.add_regular(player=0, played_time=(1, 0), img=np.zeros((1, 1)), new_tiles=new_tiles)

    def test_130(self):
        """Test 130 - Algorithm: changed tile with higher propability"""

        # H4 FJRNS
        new_tiles:BoardType = {
            (3, 7): Tile('F', 75), (4, 7): Tile('J', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75),
        }  # fmt:off
        board: BoardType = {}
        game = self.create_game()
        self.add_move(game, board, new_tiles, (0, (1, 0)))

        # 5G V.TEn
        new_tiles = {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75)}
        board.update(new_tiles)

        changed = {(4, 7): Tile('I', 85)}  # simulate changed tiles
        _recalculate_score_on_tiles_change(game=game, changed=changed)

        board = self.add_move(game, board, new_tiles, (1, (1, 1)))
        # score changed from 34 to 24
        self.assert_board_and_score(game, board, (24, 18), 2)


if __name__ == '__main__':
    unittest.main(module='test_algorithm_moves')
