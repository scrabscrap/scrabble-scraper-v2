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

from config import config

EMPTY_CONFIG = os.path.dirname(__file__) + '/test_config_empty.ini'


class ConfigTestCase(unittest.TestCase):
    '''Test class for config.py'''

    def setUp(self) -> None:
        return super().setUp()

    def test_default_values(self):
        config.reload(ini_file=EMPTY_CONFIG + '-invalid')  # only log output expected
        config.reload(ini_file=EMPTY_CONFIG, clean=True)
        self.assertEqual(config.src_dir, os.path.abspath(os.path.dirname(__file__) + '/../src'))
        self.assertEqual(config.work_dir, os.path.abspath(config.src_dir + '/../work'))
        self.assertEqual(config.log_dir, os.path.abspath(config.src_dir + '/../work/log'))
        self.assertEqual(config.web_dir, os.path.abspath(config.src_dir + '/../work/web'))
        self.assertFalse(config.simulate)
        self.assertEqual(config.simulate_path, config.work_dir + '/simulate/image-{:d}.jpg')
        self.assertFalse(config.development_recording)
        self.assertEqual(config.malus_doubt, 10)
        self.assertEqual(config.max_time, 1800)
        self.assertEqual(config.min_time, -300)
        self.assertEqual(config.doubt_timeout, 20)
        self.assertEqual(config.scrabble_verify_moves, 3)
        self.assertFalse(config.show_score)
        self.assertTrue(config.output_web)
        self.assertFalse(config.output_ftp)
        self.assertTrue(config.video_warp)
        self.assertIsNone(config.video_warp_coordinates)
        self.assertEqual(config.video_width, 992)
        self.assertEqual(config.video_height, 976)
        self.assertEqual(config.video_fps, 30)
        self.assertFalse(config.video_rotate)
        self.assertEqual(config.board_layout, 'custom')
        self.assertEqual(config.tiles_language, 'de')
        self.assertEqual(config.tiles_image_path, os.path.abspath(config.src_dir + '/game_board/img/default'))
        self.assertDictEqual(config.tiles_bag,
                             json.loads('{"A": 5, "B": 2, "C": 2, "D": 4, "E": 15, "F": 2, "G": 3, "H": 4, "I": 6, '
                                        '"J": 1, "K": 2, "L": 3, "M": 4, "N": 9, "O": 3, "P": 1, "Q": 1, "R": 6, "S": 7, '
                                        '"T": 6, "U": 6, "V": 1, "W": 1, "X": 1, "Y": 1, "Z": 1, '
                                        '"\u00c4": 1, "\u00d6": 1, "\u00dc": 1, "_": 2}'))
        self.assertDictEqual(config.tiles_scores,
                             json.loads('{"A": 1, "B": 3, "C": 4, "D": 2, "E": 1, "F": 4, "G": 2, "H": 4, "I": 1, '
                                        '"J": 8, "K": 5, "L": 1, "M": 3, "N": 1, "O": 2, "P": 3, "Q": 10, "R": 1, "S": 1, '
                                        '"T": 1, "U": 1, "V": 4, "W": 4, "X": 8, "Y": 4, "Z": 10, "_": 0}'))
        self.assertEqual(config.system_quit, 'shutdown')
        self.assertEqual(config.system_gitbranch, 'main')
        config.reload()


if __name__ == '__main__':
    unittest.main(module='test_config')
