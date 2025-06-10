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
from dataclasses import dataclass, field
from typing import Optional

DEFAULT = {
    'path': {
        'src_dir': os.path.dirname(__file__) or '.',
        'work_dir': '%(src_dir)s/../work',
        'log_dir': '%(src_dir)s/../work/log',
        'web_dir': '%(src_dir)s/../work/web',
    },
    'development': {'simulate': 'False', 'simulate_path': 'test/game01/image-{:d}.jpg', 'recording': 'False'},
    'scrabble': {
        'tournament': 'SCRABBLE SCRAPER',
        'malus_doubt': '10',
        'max_time': '1800',
        'min_time': '-300',
        'doubt_timeout': '20',
        'timeout_malus': '10',
        'verify_moves': '3',
        'show_score': 'False',
    },
    'output': {'upload_server': 'False', 'upload_modus': 'http'},
    'video': {'warp': 'True', 'width': '976', 'height': '976', 'fps': '25', 'rotate': 'True'},
    'board': {
        'layout': 'custom2012',
        'tiles_threshold': '800',
        'min_tiles_rate': '96',
        'dynamic_threshold': 'True',
        'language': 'de',
    },
    'system': {'quit': 'shutdown', 'gitbranch': 'main'},
}


def as_bool(string: str) -> bool:
    """convert boolean string to boolean value"""
    return string.lower() in ('true', 'yes')


@dataclass
class PathConfig:
    """access to path configuration"""

    config: configparser.ConfigParser

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


@dataclass
class DevelopmentConfig:
    """access to development configuration"""

    config: configparser.ConfigParser

    @property
    def simulate(self) -> bool:
        """Should Scrabscrap be simulated?"""
        return self.config.getboolean('development', 'simulate', fallback=False)

    @property
    def simulate_path(self) -> str:
        """Path pattern for simulation images"""
        return self.config.get('development', 'simulate_path', fallback='test/game01/image-{:d}.jpg')

    @property
    def recording(self) -> bool:
        """Record high-resolution images and save them to disk"""
        return self.config.getboolean('development', 'recording', fallback=as_bool(DEFAULT['development']['recording']))


@dataclass
class ScrabbleConfig:
    """access to scrabble configuration"""

    config: configparser.ConfigParser

    @property
    def tournament(self) -> str:
        """Tournament name"""
        return self.config.get('scrabble', 'tournament', fallback=DEFAULT['scrabble']['tournament'])

    @property
    def malus_doubt(self) -> int:
        """Penalty points for incorrect doubts"""
        return self.config.getint('scrabble', 'malus_doubt', fallback=int(DEFAULT['scrabble']['malus_doubt']))

    @property
    def max_time(self) -> int:
        """Maximum allowed time (in seconds)"""
        return self.config.getint('scrabble', 'max_time', fallback=int(DEFAULT['scrabble']['max_time']))

    @property
    def min_time(self) -> int:
        """Maximum overtime allowed (in seconds, negative)"""
        return self.config.getint('scrabble', 'min_time', fallback=int(DEFAULT['scrabble']['min_time']))

    @property
    def doubt_timeout(self) -> int:
        """Time window to raise a doubt (in seconds)"""
        return self.config.getint('scrabble', 'doubt_timeout', fallback=int(DEFAULT['scrabble']['doubt_timeout']))

    @property
    def timeout_malus(self) -> int:
        """Penalty points for timeout"""
        return self.config.getint('scrabble', 'timeout_malus', fallback=int(DEFAULT['scrabble']['timeout_malus']))

    @property
    def verify_moves(self) -> int:
        """Number of previous moves to check for tile corrections"""
        return self.config.getint('scrabble', 'verify_moves', fallback=int(DEFAULT['scrabble']['verify_moves']))

    @property
    def show_score(self) -> bool:
        """Should the display show the current score?"""
        return self.config.getboolean('scrabble', 'show_score', fallback=as_bool(DEFAULT['scrabble']['show_score']))


@dataclass
class OutputConfig:
    """access to output configuration"""

    config: configparser.ConfigParser

    @property
    def upload_server(self) -> bool:
        """Should results be uploaded to a server?"""
        return self.config.getboolean('output', 'upload_server', fallback=as_bool(DEFAULT['output']['upload_server']))

    @property
    def upload_modus(self) -> str:
        """Upload mode (e.g., FTP, HTTP)"""
        return self.config.get('output', 'upload_modus', fallback=DEFAULT['output']['upload_modus']).replace('"', '')


@dataclass
class VideoConfig:
    """access to video configuration"""

    config: configparser.ConfigParser

    @property
    def warp(self) -> bool:
        """Should video be warped (perspective correction)?"""
        return self.config.getboolean('video', 'warp', fallback=as_bool(DEFAULT['video']['warp']))

    @property
    def warp_coordinates(self) -> Optional[list]:
        """Stored warp coordinates for perspective transformation"""
        warp_coordinates_as_string = self.config.get('video', 'warp_coordinates', fallback=None)
        if warp_coordinates_as_string is None or len(warp_coordinates_as_string) <= 0:
            return None
        return json.loads(warp_coordinates_as_string)

    @property
    def width(self) -> int:
        """used image width"""
        return self.config.getint('video', 'width', fallback=int(DEFAULT['video']['width']))

    @property
    def height(self) -> int:
        """Video frame height"""
        return self.config.getint('video', 'height', fallback=int(DEFAULT['video']['height']))

    @property
    def fps(self) -> int:
        """Frames per second used for video capture"""
        return self.config.getint('video', 'fps', fallback=int(DEFAULT['video']['fps']))

    @property
    def rotate(self) -> bool:
        """Should the image be rotated by 180°?"""
        return self.config.getboolean('video', 'rotate', fallback=as_bool(DEFAULT['video']['rotate']))


@dataclass
class BoardConfig:
    """access to board configuration"""

    config: configparser.ConfigParser

    @property
    def layout(self) -> str:
        """Board layout configuration"""
        return self.config.get('board', 'layout', fallback=DEFAULT['board']['layout']).replace('"', '')

    @property
    def tiles_threshold(self) -> int:
        """Pixel count threshold to detect tiles"""
        return self.config.getint('board', 'tiles_threshold', fallback=int(DEFAULT['board']['tiles_threshold']))

    @property
    def min_tiles_rate(self) -> int:
        """Minimum recognition rate (percentage) for template matching"""
        return self.config.getint('board', 'min_tiles_rate', fallback=int(DEFAULT['board']['min_tiles_rate']))

    @property
    def dynamic_threshold(self) -> int:
        """Use dynamic image thresholding?"""
        return self.config.getboolean('board', 'dynamic_threshold', fallback=as_bool(DEFAULT['board']['dynamic_threshold']))

    @property
    def language(self) -> str:
        """Language of the tiles (default: German)"""
        # use german language as default
        return self.config.get('board', 'language', fallback=DEFAULT['board']['language']).replace('"', '')


@dataclass
class SystemConfig:
    """access to system configuration"""

    config: configparser.ConfigParser

    @property
    def quit(self) -> str:
        """Quit behavior (e.g., 'shutdown' or 'exit')"""
        return self.config.get('system', 'quit', fallback=DEFAULT['system']['quit']).replace('"', '')

    @property
    def gitbranch(self) -> str:
        """Git branch or tag used for updates"""
        return self.config.get('system', 'gitbranch', fallback=DEFAULT['system']['gitbranch']).replace('"', '')


@dataclass
class Config:  # pylint: disable=too-many-instance-attributes
    """access to application configuration"""

    path: PathConfig = field(init=False)
    development: DevelopmentConfig = field(init=False)
    scrabble: ScrabbleConfig = field(init=False)
    output: OutputConfig = field(init=False)
    video: VideoConfig = field(init=False)
    board: BoardConfig = field(init=False)
    system: SystemConfig = field(init=False)

    def __post_init__(self) -> None:
        self.config = configparser.ConfigParser()
        self.ini_path: str = (os.path.dirname(__file__) or '.') + '/../work/scrabble.ini'
        self.reload(ini_file=self.ini_path, clean=False)
        self.is_testing: bool = False
        self.path = PathConfig(config=self.config)
        self.development = DevelopmentConfig(config=self.config)
        self.scrabble = ScrabbleConfig(config=self.config)
        self.output = OutputConfig(config=self.config)
        self.video = VideoConfig(config=self.config)
        self.board = BoardConfig(config=self.config)
        self.system = SystemConfig(config=self.config)

    def reload(self, ini_file=None, clean=True) -> None:
        """reload configuration"""
        if clean:
            self.config.clear()
        self.config.read_dict(DEFAULT)
        try:
            self.ini_path = ini_file or self.ini_path
            logging.info(f'reload {self.ini_path}')
            with open(self.ini_path, encoding='UTF-8') as config_file:
                self.config.read_file(config_file)
        except OSError as oops:
            logging.error(f'can not read INI-File {self.ini_path}: error({oops.errno}): {oops.strerror}')

    def save(self) -> None:  # pragma: no cover
        """save configuration"""
        with open(self.ini_path, 'w', encoding='UTF-8') as config_file:
            config_save = configparser.ConfigParser()  # store only changed settings
            for section in self.config.sections():
                config_save.add_section(section=section)
                for option in self.config.options(section=section):
                    if self.config.get(section, option) != DEFAULT[section][option] and section not in ('DEFAULT', 'path'):
                        config_save.set(section, option, self.config.get(section, option))
            config_save.write(config_file)


class VersionInfo:
    """version information"""

    def __init__(self) -> None:
        version_info = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        self._git_commit = version_info.stdout.strip() if version_info.returncode == 0 else 'n/a'
        # fmt: off
        branch_info = subprocess.run( ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        self._git_branch = branch_info.stdout.strip() if branch_info.returncode == 0 else 'n/a'
        version_info = subprocess.run( ['git', 'describe', '--tags', '--dirty', '--abbrev=4', '--always'],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        # fmt:on
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
