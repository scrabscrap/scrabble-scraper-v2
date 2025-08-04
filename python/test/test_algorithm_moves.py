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

from analyzer import filter_candidates
from move import Tile
from state import GameState, State
from test.test_base import BaseTestClass


class AlgorithmMovesTestCase(BaseTestClass):
    """
    Unit tests for Scrabble move processing algorithm.

    This test case simulates Scrabble games using mock implementations for image processing and camera input.
    It verifies correct board updates, score calculations, and game state transitions for various move scenarios,
    including edge cases such as challenges, blank tiles, and board boundaries.
    """

    def test_102(self):
        """Test 102 - Algorithm: first move"""
        # H4 FIRNS
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 }
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_103(self):
        """Test 103 - Algorithm: crossed move"""
        # H4 FIRNS
        # 5G V.TEN
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (24, 20),
                   'tiles': {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75)},
                 }                                    
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_104(self):
        """Test 104 - Algorithm: move at top (horizontal)"""
        # H4 TURNeNS
        # 8A SAUNIER.
        # A8 .UPER
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
                              (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 74),
                   'tiles': { (7, 0): Tile('S', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
                              (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75), },
                 },
                 { 'button': 'GREEN', 'score': (73, 74),
                   'tiles': { (8, 0): Tile('U', 75), (9, 0): Tile('P', 75), (10, 0): Tile('E', 75), (11, 0): Tile('R', 75) },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_105(self):
        """Test 105 - Algorithm: move at top (vertical)"""
        # H4 TURNeNS
        # 8A SAUNIER.
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
                              (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 74),
                   'tiles': { (7, 0): Tile('S', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
                              (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_106(self):
        """Test 106 - Algorithm: move at bottom (horizontal)"""
        # H2 TURNeNS
        # 8H .AUNIERE
        # O5 SUP.R
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (1, 7): Tile('T', 75), (2, 7): Tile('U', 75), (3, 7): Tile('R', 75), (4, 7): Tile('N', 75),
                              (5, 7): Tile('_', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 74),
                   'tiles': { (7, 8): Tile('A', 75), (7, 9): Tile('U', 75), (7, 10): Tile('N', 75), (7, 11): Tile('I', 75),
                              (7, 12): Tile('E', 75), (7, 13): Tile('R', 75), (7, 14): Tile('E', 75), },
                 },
                 { 'button': 'GREEN', 'score': (72, 77),
                   'tiles': { (4, 14): Tile('S', 75), (5, 14): Tile('U', 75), (6, 14): Tile('P', 75), (8, 14): Tile('R', 75) },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_107(self):
        """Test 107 - Algorithm: move at bottom (vertical)"""
        # H2 TURNeNS
        # 8H .AUNIERE
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (1, 7): Tile('T', 75), (2, 7): Tile('U', 75), (3, 7): Tile('R', 75), (4, 7): Tile('N', 75),
                              (5, 7): Tile('_', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 77),
                   'tiles': { (7, 8): Tile('A', 75), (7, 9): Tile('U', 75), (7, 10): Tile('N', 75), (7, 11): Tile('I', 75),
                              (7, 12): Tile('E', 75), (7, 13): Tile('R', 75), (7, 14): Tile('E', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_108(self):
        """Test 108 - Algorithm: move at left border (horizontal)"""
        # 8D TURNeNS
        # H1 SAUNIER.
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (7, 3): Tile('T', 75), (7, 4): Tile('U', 75), (7, 5): Tile('R', 75), (7, 6): Tile('N', 75),
                              (7, 7): Tile('_', 75), (7, 8): Tile('N', 75), (7, 9): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 74),
                   'tiles': { (0, 7): Tile('S', 75), (1, 7): Tile('A', 75), (2, 7): Tile('U', 75), (3, 7): Tile('N', 75),
                              (4, 7): Tile('I', 75), (5, 7): Tile('E', 75), (6, 7): Tile('R', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_109(self):
        """Test 109 - Algorithm: move at left border (vertical)"""
        # 8D TURNeNS
        # H1 SAUNIER.
        # 1H .UPER
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (7, 3): Tile('T', 75), (7, 4): Tile('U', 75), (7, 5): Tile('R', 75), (7, 6): Tile('N', 75),
                              (7, 7): Tile('_', 75), (7, 8): Tile('N', 75), (7, 9): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 74),
                   'tiles': { (0, 7): Tile('S', 75), (1, 7): Tile('A', 75), (2, 7): Tile('U', 75), (3, 7): Tile('N', 75),
                              (4, 7): Tile('I', 75), (5, 7): Tile('E', 75), (6, 7): Tile('R', 75), },
                 },
                 { 'button': 'GREEN', 'score': (73, 74),
                   'tiles': {  (0, 8): Tile('U', 75), (0, 9): Tile('P', 75), (0, 10): Tile('E', 75), (0, 11): Tile('R', 75)},
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_110(self):
        """Test 110 - Algorithm: move at right border (horizontal)"""
        # 8B TURNeNS
        # H8 .AUNIERE
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (7, 1): Tile('T', 75), (7, 2): Tile('U', 75), (7, 3): Tile('R', 75), (7, 4): Tile('N', 75),
                              (7, 5): Tile('_', 75), (7, 6): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 77),
                   'tiles': { (8, 7): Tile('A', 75), (9, 7): Tile('U', 75), (10, 7): Tile('N', 75), (11, 7): Tile('I', 75),
                              (12, 7): Tile('E', 75), (13, 7): Tile('R', 75), (14, 7): Tile('E', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_111(self):
        """Test 111 - Algorithm: move at right border (vertical)"""
        # 8B TURNeNS
        # H8 .AUNIERE
        # 15E SUP.R
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (7, 1): Tile('T', 75), (7, 2): Tile('U', 75), (7, 3): Tile('R', 75), (7, 4): Tile('N', 75),
                              (7, 5): Tile('_', 75), (7, 6): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 77),
                   'tiles': { (8, 7): Tile('A', 75), (9, 7): Tile('U', 75), (10, 7): Tile('N', 75), (11, 7): Tile('I', 75),
                              (12, 7): Tile('E', 75), (13, 7): Tile('R', 75), (14, 7): Tile('E', 75), },
                 },
                 { 'button': 'GREEN', 'score': (72, 77),
                   'tiles': { (14, 4): Tile('S', 75), (14, 5): Tile('U', 75), (14, 6): Tile('P', 75), (14, 8): Tile('R', 75) },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_112(self):
        """Test 112 - Algorithm: challenge without move"""

        data = [ { 'button': 'YELLOW', 'score': (0, 0), 'tiles': {}, },
                 { 'button': 'DOUBT0', 'score': (0, 0), 'tiles': {}, },
                 { 'button': 'YELLOW', 'score': (0, 0), 'tiles': {}, },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(len(State.ctx.game.moves), 0, 'expected no moves')
        self.assertEqual(State.ctx.current_state, GameState.S0, 'excpected Status Green')

    def test_113(self):
        """Test 113 - Algorithm: not enough point for a challenge"""
        # H4 FIRNS
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), }, 
                 },
                 { 'button': 'YELLOW', 'score': (24, 0), 'tiles': {}, },
                 { 'button': 'DOUBT0', 'score': (24, -10), 'tiles': {}, },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_114(self):
        """Test 114 - Algorithm: valid challenge"""
        # H4 FIRNS
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), }, 
                 },
                 { 'button': 'YELLOW', 'score': (24, 0), 'tiles': {}, },
                 { 'button': 'DOUBT1', 'score': (0, 0), 'tiles': {}, },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_115(self):
        """Test 115 - Algorithm: invalid challenge"""
        # H4 FIRNS
        # 5G V.TEN
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (24, 20),
                   'tiles': {  (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75) },
                 },
                 { 'button': 'YELLOW', 'score': (24, 20), 'tiles': {}, },
                 { 'button': 'DOUBT1', 'score': (14, 20), 'tiles': {}, },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_116(self):
        """Test 116 - Algorithm: valid callenge - tiles not removed"""
        # currently not supported
        pass

    def test_117(self):
        """Test 117 - Algorithm: extend a word"""
        # H5 TEST
        # H5 ....ER
        data = [ { 'button': 'GREEN', 'score': (8, 0),
                   'tiles': { (4, 7): Tile('T', 75), (5, 7): Tile('E', 75), (6, 7): Tile('S', 75), (7, 7): Tile('T', 75) },
                 },
                 { 'button': 'RED', 'score': (8, 6),
                   'tiles': { (8, 7): Tile('E', 75), (9, 7): Tile('R', 75) },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_118(self):
        """Test 118 - Algorithm: word between two word"""
        # H5 TEST
        # 5H .AT
        # 8H .UT
        # J5 .ES.
        data = [ { 'button': 'GREEN', 'score': (8, 0),
                   'tiles': { (4, 7): Tile('T', 75), (5, 7): Tile('E', 75), (6, 7): Tile('S', 75), (7, 7): Tile('T', 75) },
                 },
                 { 'button': 'RED', 'score': (8, 3),
                   'tiles': {(4, 8): Tile('A', 75), (4, 9): Tile('T', 75)},
                 },
                 { 'button': 'GREEN', 'score': (11, 3),
                   'tiles': {(7, 8): Tile('U', 75), (7, 9): Tile('T', 75)},
                 },
                 { 'button': 'RED', 'score': (11, 9),
                   'tiles': {(5, 9): Tile('E', 75), (6, 9): Tile('S', 75)},
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_119(self):
        """Test 119 - Algorithm: calculation double letter"""
        # H4 FIRNS
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 }, 
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_120(self):
        """Test 120 - Algorithm: calculation triple letter"""
        # H4 TURNeNS
        # 6B SAUNIE.E
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
                              (7, 7): Tile('_', 75), (8, 7): Tile('N', 75),(9, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 62),
                   'tiles': { (5, 1): Tile('S', 75), (5, 2): Tile('A', 75), (5, 3): Tile('U', 75), (5, 4): Tile('N', 75),
                              (5, 5): Tile('I', 75), (5, 6): Tile('E', 75), (5, 8): Tile('E', 75), },
                 },                     
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_121(self):
        """Test 121 - Algorithm: calculation double word"""
        # H4 FIRNS
        # 5G V.TEN
        data = [ { 'button': 'GREEN', 'score': (24, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (24, 20),
                   'tiles': {(4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('N', 75)},
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_122(self):
        """Test 122 - Algorithm: calculation triple word"""
        # H4 TURNeNS
        # 8A SAUNIER.
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
                              (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 74),
                   'tiles': { (7, 0): Tile('S', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
                              (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_123(self):
        """Test 123 - Algorithm: calculation double letter (blank on double letter field)"""
        # H4 fIRNS
        data = [ { 'button': 'GREEN', 'score': (8, 0),
                   'tiles': { (3, 7): Tile('_', 75), (4, 7): Tile('I', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_124(self):
        """Test 124 - Algorithm: calculation triple letter (blank on double letter field)"""
        # H4 TURNENS
        # 6B sAUNiE.E
        data = [ { 'button': 'GREEN', 'score': (66, 0),
                   'tiles': { (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
                              (7, 7): Tile('E', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (66, 56),
                   'tiles': { (5, 1): Tile('_', 75), (5, 2): Tile('A', 75), (5, 3): Tile('U', 75), (5, 4): Tile('N', 75),
                              (5, 5): Tile('_', 75), (5, 6): Tile('E', 75), (5, 8): Tile('E', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_125(self):
        """Test 125 - Algorithm: calculation double word (blank on double letter field)"""
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
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_126(self):
        """Test 126 - Algorithm: calculation triple word (blank on double letter field)"""
        # H4 TURNeNS
        # 8A sAUNIER.
        data = [ { 'button': 'GREEN', 'score': (64, 0),
                   'tiles': { (3, 7): Tile('T', 75), (4, 7): Tile('U', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75),
                              (7, 7): Tile('_', 75), (8, 7): Tile('N', 75), (9, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (64, 71),
                   'tiles': { (7, 0): Tile('_', 75), (7, 1): Tile('A', 75), (7, 2): Tile('U', 75), (7, 3): Tile('N', 75),
                              (7, 4): Tile('I', 75), (7, 5): Tile('E', 75), (7, 6): Tile('R', 75), },
                 },
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    # def test_127(self):
    #     """Test 127 - Algorithm: tile removed without challenge"""
    #     pass

    # def test_128(self):
    #     """Test 128 - Algorithm: tile removed without challenge and put again to board"""
    #     pass

    def test_129(self):
        """Test 129 - Algorithm: space between new tiles"""

        # simulate filtering in _image_processing
        data = [ { 'button': 'GREEN', 'score': (6, 0),
                   'tiles': { (3, 7): Tile('F', 75), (5, 7): Tile('R', 75), (6, 7): Tile('N', 75), (7, 7): Tile('S', 75) },
                 },
                ]  # fmt:off
        tiles = data[-1]['tiles']
        tiles_candidates = filter_candidates((7, 7), set(tiles), set())
        tiles = {k: v for k, v in tiles.items() if k in tiles_candidates}
        data[-1]['tiles'] = tiles
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')

    def test_130(self):
        """Test 130 - Algorithm: changed tile with higher propability"""
        # H4 FÄRNS -> FIRNS
        # 5G V.TEn
        data = [ { 'button': 'GREEN', 'score': (34, 0),
                   'tiles': { (3, 7): Tile('F', 75), (4, 7): Tile('Ä', 75), (5, 7): Tile('R', 75),
                              (6, 7): Tile('N', 75), (7, 7): Tile('S', 75), },
                 },
                 { 'button': 'RED', 'score': (24, 18),
                   'tiles': { (4, 6): Tile('V', 75), (4, 8): Tile('T', 75), (4, 9): Tile('E', 75), (4, 10): Tile('_', 75), (4, 7): Tile('I', 85) },
                 }                                    
                ]  # fmt:off
        self.run_data(start_button='red', data=data)
        self.assertEqual(State.ctx.game.moves[-1].score, data[-1]['score'], 'invalid scores')


if __name__ == '__main__':
    unittest.main(module='test_algorithm_moves')
