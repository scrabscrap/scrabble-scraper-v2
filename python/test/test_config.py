"""
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
"""

import json
import os
import unittest

from config import config

EMPTY_CONFIG = os.path.dirname(__file__) + '/test_config_empty.ini'


class ConfigTestCase(unittest.TestCase):
    """Test class for config.py"""

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
        # self.assertEqual(config.simulate_path, config.work_dir + '/simulate/image-{:d}.jpg')
        self.assertFalse(config.development_recording)
        self.assertEqual(config.malus_doubt, 10)
        self.assertEqual(config.max_time, 1800)
        self.assertEqual(config.min_time, -300)
        self.assertEqual(config.doubt_timeout, 20)
        self.assertEqual(config.verify_moves, 3)
        self.assertFalse(config.show_score)
        self.assertFalse(config.upload_server)
        self.assertEqual(config.upload_modus, 'http')
        self.assertTrue(config.video_warp)
        self.assertIsNone(config.video_warp_coordinates)
        self.assertEqual(config.video_width, 976)
        self.assertEqual(config.video_height, 976)
        self.assertEqual(config.video_fps, 25)
        self.assertTrue(config.video_rotate)
        self.assertEqual(config.board_layout, 'custom2012')
        self.assertEqual(config.board_language, 'de')
        self.assertEqual(config.system_quit, 'shutdown')
        self.assertEqual(config.system_gitbranch, 'main')
        config.reload()


if __name__ == '__main__':
    unittest.main(module='test_config')
