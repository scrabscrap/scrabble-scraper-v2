'''
 This file is part of the scrabble-scraper-v2 distribution
 (https://github.com/scrabscrap/scrabble-scraper-v2)
 Copyright (c) 2023 Rainer Rohloff.

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, version 3.

 This program is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.
'''
import json
import os
import unittest

from config import Config

EMPTY_CONFIG = os.path.dirname(__file__) + '/test_config_empty.ini'


class ConfigTestCase(unittest.TestCase):
    '''Test class for config.py'''

    def setUp(self) -> None:
        return super().setUp()

    def test_default_values(self):
        Config.reload(ini_file=EMPTY_CONFIG + '-invalid')  # only log output expected
        Config.reload(ini_file=EMPTY_CONFIG, clean=True)
        self.assertEqual(Config.src_dir(), os.path.abspath(os.path.dirname(__file__) + '/../src'))
        self.assertEqual(Config.work_dir(), os.path.abspath(Config.src_dir() + '/../work'))
        self.assertEqual(Config.log_dir(), os.path.abspath(Config.src_dir() + '/../work/log'))
        self.assertEqual(Config.web_dir(), os.path.abspath(Config.src_dir() + '/../work/web'))
        self.assertFalse(Config.simulate())
        # self.assertEqual(config.simulate_path, config.work_dir + '/simulate/image-{:d}.jpg')
        self.assertFalse(Config.development_recording())
        self.assertEqual(Config.malus_doubt(), 10)
        self.assertEqual(Config.max_time(), 1800)
        self.assertEqual(Config.min_time(), -300)
        self.assertEqual(Config.doubt_timeout(), 20)
        self.assertEqual(Config.scrabble_verify_moves(), 3)
        self.assertFalse(Config.show_score())
        self.assertFalse(Config.upload_server())
        self.assertEqual(Config.upload_modus(), 'http')
        self.assertTrue(Config.video_warp())
        self.assertIsNone(Config.video_warp_coordinates())
        self.assertEqual(Config.video_width(), 912)
        self.assertEqual(Config.video_height(), 912)
        self.assertEqual(Config.video_fps(), 30)
        self.assertFalse(Config.video_rotate())
        self.assertEqual(Config.board_layout(), 'custom2012')
        self.assertEqual(Config.tiles_language(), 'de')
        self.assertEqual(Config.tiles_image_path(), os.path.abspath(Config.src_dir() + '/game_board/img/default'))
        self.assertDictEqual(Config.tiles_bag(),
                             json.loads('{"A": 5, "B": 2, "C": 2, "D": 4, "E": 15, "F": 2, "G": 3, "H": 4, "I": 6, '
                                        '"J": 1, "K": 2, "L": 3, "M": 4, "N": 9, "O": 3, "P": 1, "Q": 1, "R": 6, "S": 7, '
                                        '"T": 6, "U": 6, "V": 1, "W": 1, "X": 1, "Y": 1, "Z": 1, '
                                        '"\u00c4": 1, "\u00d6": 1, "\u00dc": 1, "_": 2}'))
        self.assertDictEqual(Config.tiles_scores(),
                             json.loads('{"A": 1, "B": 3, "C": 4, "D": 2, "E": 1, "F": 4, "G": 2, "H": 4, "I": 1, '
                                        '"J": 8, "K": 5, "L": 1, "M": 3, "N": 1, "O": 2, "P": 3, "Q": 10, "R": 1, "S": 1, '
                                        '"T": 1, "U": 1, "V": 4, "W": 4, "X": 8, "Y": 4, "Z": 10, "_": 0}'))
        self.assertEqual(Config.system_quit(), 'shutdown')
        self.assertEqual(Config.system_gitbranch(), 'main')
        Config.reload()


if __name__ == '__main__':
    unittest.main(module='test_config')
