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
from pathlib import Path
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
        self.assertEqual(config.path.src_dir, Path(__file__).resolve().parent.parent / 'src')
        self.assertEqual(config.path.work_dir, (config.path.src_dir.parent / 'work').resolve())
        self.assertEqual(config.path.log_dir, (config.path.src_dir.parent / 'work' / 'log').resolve())
        self.assertEqual(config.path.web_dir, (config.path.src_dir.parent / 'work' / 'web').resolve())
        self.assertFalse(config.development.simulate)
        # self.assertEqual(config.simulate_path, config.work_dir + '/simulate/image-{:d}.jpg')
        self.assertFalse(config.development.recording)
        self.assertEqual(config.scrabble.malus_doubt, 10)
        self.assertEqual(config.scrabble.max_time, 1800)
        self.assertEqual(config.scrabble.min_time, -300)
        self.assertEqual(config.scrabble.doubt_timeout, 20)
        self.assertEqual(config.scrabble.verify_moves, 3)
        self.assertFalse(config.scrabble.show_score)
        self.assertFalse(config.output.upload_server)
        self.assertEqual(config.output.upload_modus, 'http')
        self.assertTrue(config.video.warp)
        self.assertIsNone(config.video.warp_coordinates)
        self.assertEqual(config.video.width, 976)
        self.assertEqual(config.video.height, 976)
        self.assertEqual(config.video.fps, 25)
        self.assertTrue(config.video.rotate)
        self.assertEqual(config.board.layout, 'custom2012')
        self.assertEqual(config.board.language, 'de')
        self.assertEqual(config.system.quit, 'shutdown')
        self.assertEqual(config.system.gitbranch, 'main')
        config.reload()


if __name__ == '__main__':
    unittest.main(module='test_config')
