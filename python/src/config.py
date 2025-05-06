"""
This file is part of the scrabble-scraper-v2 distribution
(https://github.com/scrabscrap/scrabble-scraper-v2)
Copyright (c) 2022 Rainer Rohloff.

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

import configparser
import json
import logging
import os
import subprocess
from typing import Optional


class Config:  # pylint: disable=too-many-public-methods
    """access to application configuration"""

    defaults = {
        'development.recording': False,
        'scrabble.tournament': 'SCRABBLE SCRAPER',
        'scrabble.malus_doubt': 10,
        'scrabble.max_time': 1800,
        'scrabble.min_time': -300,
        'scrabble.doubt_timeout': 20,
        'scrabble.timeout_malus': 10,
        'scrabble.verify_moves': 3,
        'scrabble.show_score': False,
        'output.upload_server': False,
        'output.upload_modus': 'http',
        'video.warp': True,
        'video.width': 928,
        'video.height': 912,
        'video.fps': 30,
        'video.rotate': False,
        'board.layout': 'custom2012',
        'board.tiles_threshold': 800,
        'board.min_tiles_rate': 96,
        'board.dynamic_threshold': True,
        'system.quit': 'shutdown',
        'system.gitbranch': 'main',
        'tiles.language': 'de',
    }

    def __init__(self, ini_file=None) -> None:
        self.config = configparser.ConfigParser()
        self.ini_path: str = ini_file if ini_file is not None else f'{self.work_dir}/scrabble.ini'
        self.reload(ini_file=ini_file, clean=False)
        self.is_testing: bool = False

    def reload(self, ini_file=None, clean=True) -> None:
        """reload configuration from file"""
        if clean:
            self.config.clear()
        try:
            self.config['path'] = {'src_dir': os.path.dirname(__file__) or '.'}
            self.ini_path = ini_file or self.ini_path
            logging.info(f'reload {self.ini_path}')
            with open(self.ini_path, 'r', encoding='UTF-8') as config_file:
                self.config.read_file(config_file)
        except OSError as oops:
            logging.error(f'can not read INI-File: error({oops.errno}): {oops.strerror}')

    def save(self) -> None:  # pragma: no cover
        """save configuration to file"""
        with open(self.ini_path, 'w', encoding='UTF-8') as config_file:
            val = self.config['path']['src_dir']
            if self.config.has_section('git'):  # cleanup old configs
                if self.config.has_option('git', 'commit'):
                    self.config.remove_option('git', 'commit')
                self.config.remove_section('git')
            if val == (os.path.dirname(__file__) or '.'):
                self.config.remove_option('path', 'src_dir')
                self.config.write(config_file)
                self.config['path']['src_dir'] = val
            else:
                self.config.write(config_file)

    # unused:
    # @property
    # def config_as_dict(self) -> dict:
    #     """get configuration as dict"""
    #     return {s: dict(self.config.items(s)) for s in self.config.sections()}

    @property
    def src_dir(self) -> str:
        """Get source directory"""
        return os.path.abspath(self.config.get('path', 'src_dir', fallback=os.path.dirname(__file__) or '.'))

    @property
    def work_dir(self) -> str:
        """Get working directory"""
        return os.path.abspath(self.config.get('path', 'work_dir', fallback=f'{self.src_dir}/../work'))

    @property
    def log_dir(self) -> str:
        """Get log directory"""
        return os.path.abspath(self.config.get('path', 'log_dir', fallback=f'{self.src_dir}/../work/log'))

    @property
    def web_dir(self) -> str:
        """Get web output directory"""
        return os.path.abspath(self.config.get('path', 'web_dir', fallback=f'{self.src_dir}/../work/web'))

    @property
    def simulate(self) -> bool:
        """Should Scrabscrap be simulated?"""
        return self.config.getboolean('development', 'simulate', fallback=False)

    @property
    def simulate_path(self) -> str:
        """Path pattern for simulation images"""
        return self.config.get('development', 'simulate_path', fallback=self.src_dir + '/../test/game01/image-{:d}.jpg')

    @property
    def development_recording(self) -> bool:
        """Record high-resolution images and save them to disk"""
        return self.config.getboolean('development', 'recording', fallback=self.defaults['development.recording'])  # type: ignore

    @property
    def tournament(self) -> str:
        """Tournament name"""
        return self.config.get('scrabble', 'tournament', fallback=self.defaults['scrabble.tournament'])  # type: ignore

    @property
    def malus_doubt(self) -> int:
        """Penalty points for incorrect doubts"""
        return self.config.getint('scrabble', 'malus_doubt', fallback=self.defaults['scrabble.malus_doubt'])  # type: ignore

    @property
    def max_time(self) -> int:
        """Maximum allowed time (in seconds)"""
        return self.config.getint('scrabble', 'max_time', fallback=self.defaults['scrabble.max_time'])  # type: ignore

    @property
    def min_time(self) -> int:
        """Maximum overtime allowed (in seconds, negative)"""
        return self.config.getint('scrabble', 'min_time', fallback=self.defaults['scrabble.min_time'])  # type: ignore

    @property
    def doubt_timeout(self) -> int:
        """Time window to raise a doubt (in seconds)"""
        return self.config.getint('scrabble', 'doubt_timeout', fallback=self.defaults['scrabble.doubt_timeout'])  # type: ignore

    @property
    def timeout_malus(self) -> int:
        """Penalty points for timeout"""
        return self.config.getint('scrabble', 'timeout_malus', fallback=self.defaults['scrabble.timeout_malus'])  # type: ignore

    @property
    def scrabble_verify_moves(self) -> int:
        """Number of previous moves to check for tile corrections"""
        return self.config.getint('scrabble', 'verify_moves', fallback=self.defaults['scrabble.verify_moves'])  # type: ignore

    @property
    def show_score(self) -> bool:
        """Should the display show the current score?"""
        return self.config.getboolean('scrabble', 'show_score', fallback=self.defaults['scrabble.show_score'])  # type: ignore

    @property
    def upload_server(self) -> bool:
        """Should results be uploaded to a server?"""
        return self.config.getboolean('output', 'upload_server', fallback=self.defaults['output.upload_server'])  # type: ignore

    @property
    def upload_modus(self) -> str:
        """Upload mode (e.g., FTP, HTTP)"""
        return self.config.get('output', 'upload_modus', fallback=self.defaults['output.upload_modus']).replace('"', '')  # type: ignore

    @property
    def video_warp(self) -> bool:
        """Should video be warped (perspective correction)?"""
        return self.config.getboolean('video', 'warp', fallback=self.defaults['video.warp'])  # type: ignore

    @property
    def video_warp_coordinates(self) -> Optional[list]:
        """Stored warp coordinates for perspective transformation"""
        warp_coordinates_as_string = self.config.get('video', 'warp_coordinates', fallback=None)
        if warp_coordinates_as_string is None or len(warp_coordinates_as_string) <= 0:
            return None
        return json.loads(warp_coordinates_as_string)

    @property
    def video_width(self) -> int:
        """used image width"""
        return self.config.getint('video', 'width', fallback=self.defaults['video.width'])  # type: ignore

    @property
    def video_height(self) -> int:
        """Video frame height"""
        return self.config.getint('video', 'height', fallback=self.defaults['video.height'])  # type: ignore

    @property
    def video_fps(self) -> int:
        """Frames per second used for video capture"""
        return self.config.getint('video', 'fps', fallback=self.defaults['video.fps'])  # type: ignore

    @property
    def video_rotate(self) -> bool:
        """Should the image be rotated by 180°?"""
        return self.config.getboolean('video', 'rotate', fallback=self.defaults['video.rotate'])  # type: ignore

    @property
    def board_layout(self) -> str:
        """Board layout configuration"""
        return self.config.get('board', 'layout', fallback=self.defaults['board.layout']).replace('"', '')  # type: ignore

    @property
    def board_tiles_threshold(self) -> int:
        """Pixel count threshold to detect tiles"""
        return self.config.getint('board', 'tiles_threshold', fallback=self.defaults['board.tiles_threshold'])  # type: ignore

    @property
    def board_min_tiles_rate(self) -> int:
        """Minimum recognition rate (percentage) for template matching"""
        return self.config.getint('board', 'min_tiles_rate', fallback=self.defaults['board.min_tiles_rate'])  # type: ignore

    @property
    def board_dynamic_threshold(self) -> int:
        """Use dynamic image thresholding?"""
        return self.config.getboolean('board', 'dynamic_threshold', fallback=self.defaults['board.dynamic_threshold'])  # type: ignore

    @property
    def tiles_language(self) -> str:
        """Language of the tiles (default: German)"""
        # use german language as default
        return self.config.get('tiles', 'language', fallback=self.defaults['tiles.language']).replace('"', '')  # type: ignore

    @property
    def tiles_image_path(self) -> str:
        """where to find the images for the tiles"""
        # use builtin path as default
        return self.config.get('tiles', 'image_path', fallback=f'{self.src_dir}/game_board/img/default')

    @property
    def tiles_bag(self) -> dict:
        """how many tiles are in the bag"""
        # use german tiles as default
        bag_as_str = self.config.get(
            self.tiles_language,
            'bag',
            fallback='{"A": 5, "B": 2, "C": 2, "D": 4, "E": 15, "F": 2, "G": 3, "H": 4, "I": 6, '
            '"J": 1, "K": 2, "L": 3, "M": 4, "N": 9, "O": 3, "P": 1, "Q": 1, "R": 6, "S": 7, '
            '"T": 6, "U": 6, "V": 1, "W": 1, "X": 1, "Y": 1, "Z": 1, '
            '"\u00c4": 1, "\u00d6": 1, "\u00dc": 1, "_": 2}',
        )
        return json.loads(bag_as_str)

    @property
    def tiles_scores(self) -> dict:
        """ "scores for the tiles"""
        # use german tiles as default
        bag_as_str = self.config.get(
            self.tiles_language,
            'scores',
            fallback='{"A": 1, "B": 3, "C": 4, "D": 1, "E": 1, "F": 4, "G": 2, "H": 2, "I": 1,'
            '"J": 6, "K": 4, "L": 2, "M": 3, "N": 1, "O": 2, "P": 4, "Q": 10, "R": 1,'
            '"S": 1, "T": 1, "U": 1, "V": 6, "W": 3, "X": 8, "Y": 10, "Z": 3,'
            '"\u00c4": 6, "\u00d6": 8, "\u00dc": 6, "_": 0}',
        )
        return json.loads(bag_as_str)

    @property
    def system_quit(self) -> str:
        """Quit behavior (e.g., 'shutdown' or 'exit')"""
        return self.config.get('system', 'quit', fallback=self.defaults['system.quit']).replace('"', '')  # type: ignore

    @property
    def system_gitbranch(self) -> str:
        """Git branch or tag used for updates"""
        return self.config.get('system', 'gitbranch', fallback=self.defaults['system.gitbranch']).replace('"', '')  # type: ignore


class VersionInfo:
    """version information"""

    def __init__(self) -> None:
        version_info = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        self._git_commit = version_info.stdout.strip() if version_info.returncode == 0 else 'n/a'
        branch_info = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self._git_branch = branch_info.stdout.strip() if branch_info.returncode == 0 else 'n/a'
        version_info = subprocess.run(
            ['git', 'describe', '--tags', '--dirty', '--abbrev=4', '--always'],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self._git_version = version_info.stdout.strip() if version_info.returncode == 0 else 'n/a'

    @property
    def git_commit(self) -> str:
        """git commit hash"""
        return self._git_commit

    @property
    def git_branch(self) -> str:
        """git branch"""
        return self._git_branch

    @property
    def git_version(self) -> str:
        """git branch"""
        return self._git_version

    @property
    def git_dirty(self) -> bool:
        """git branch"""
        return self._git_version.endswith('dirty')


config = Config()
version = VersionInfo()
