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

from __future__ import annotations

import configparser
import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# fmt: off
SCORES = {
    'de': { 'A': 1, 'B': 3, 'C': 4, 'D': 1, 'E': 1, 'F': 4, 'G': 2, 'H': 2,
            'I': 1, 'J': 6, 'K': 4, 'L': 2, 'M': 3, 'N': 1, 'O': 2, 'P': 4,
            'Q': 10,'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 6, 'W': 3, 'X': 8,
            'Y': 10, 'Z': 3, '\u00c4': 6, '\u00d6': 8, '\u00dc': 6, '_': 0,
    },
    'en': { 'A': 1, 'B': 3, 'C': 4, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4,
            'I': 1, 'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 2, 'P': 3,
            'Q': 10,'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8,
            'Y': 4, 'Z': 10, '_': 0,
    },
    'fr': { 'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4,
            'I': 1, 'J': 8, 'K': 10,'L': 1, 'M': 2, 'N': 1, 'O': 2, 'P': 3,
            'Q': 8, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 10,'X': 10,
            'Y': 10,'Z': 10,'_': 0,
    },
    'es': { 'A': 1, 'B': 3, 'C': 3,'CH': 5, 'D': 2, 'E': 1, 'F': 4, 'G': 2,
            'H': 4, 'I': 1, 'J': 8, 'L': 1,'LL': 8, 'M': 3, 'N': 1, '\u00d1': 8,
            'O': 1, 'P': 3, 'Q': 5, 'R': 1,'RR': 8, 'S': 1, 'T': 1, 'U': 1,
            'V': 4, 'X': 8, 'Y': 4, 'Z': 10,'_': 0,
    },
}

BAGS = {
    'de': { 'A': 5, 'B': 2, 'C': 2, 'D': 4, 'E': 15,'F': 2, 'G': 3, 'H': 4,
            'I': 6, 'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 9, 'O': 3, 'P': 1,
            'Q': 1, 'R': 6, 'S': 7, 'T': 6, 'U': 6, 'V': 1, 'W': 1, 'X': 1,
            'Y': 1, 'Z': 1, '\u00c4': 1, '\u00d6': 1, '\u00dc': 1, '_': 2,
    },
    'en': { 'A': 9, 'B': 2, 'C': 2, 'D': 4, 'E': 12,'F': 2, 'G': 3, 'H': 2,
            'I': 9, 'J': 1, 'K': 1, 'L': 4, 'M': 2, 'N': 6, 'O': 8, 'P': 2,
            'Q': 1, 'R': 6, 'S': 4, 'T': 6, 'U': 4, 'V': 2, 'W': 2, 'X': 1,
            'Y': 2, 'Z': 1, '_': 2,
    },
    'fr': { 'A': 9, 'B': 2, 'C': 2, 'D': 3, 'E': 15,'F': 2, 'G': 2, 'H': 2,
            'I': 8, 'J': 1, 'K': 1, 'L': 5, 'M': 3, 'N': 6, 'O': 6, 'P': 2,
            'Q': 1, 'R': 6, 'S': 6, 'T': 6, 'U': 6, 'V': 2, 'W': 1, 'X': 1,
            'Y': 1, 'Z': 1, '_': 2,
    },
    'es': { 'A': 12,'B': 2, 'C': 4,'CH': 1, 'D': 5, 'E': 12,'F': 1, 'G': 2,
            'H': 2, 'I': 6, 'J': 1, 'L': 4,'LL': 1, 'M': 2, 'N': 5,'\u00d1': 1,
            'O': 9, 'P': 2, 'Q': 1, 'R': 5,'RR': 1, 'S': 6, 'T': 4, 'U': 5,
            'V': 1, 'X': 1, 'Y': 1, 'Z': 1, '_': 2,
    },
}

# triple words/double words/triple letter/double letter field coordinates
TRIPLE_WORDS = {(0, 0), (7, 0), (14, 0), (0, 7), (14, 7), (0, 14), (7, 14), (14, 14)}
DOUBLE_WORDS = {(1, 1),(13, 1), (2, 2), (12, 2), (3, 3), (11, 3), (4, 4), (10, 4), (7, 7),
                (4, 10),(10, 10),(3, 11),(11, 11),(2, 12), (12, 12), (1, 13),(13, 13), }
TRIPLE_LETTER = {(5, 1), (9, 1), (1, 5), (5, 5), (9, 5), (13, 5), (1, 9), (5, 9), (9, 9), (13, 9), (5, 13), (9, 13)}
DOUBLE_LETTER = {(3, 0),(11, 0), (6, 2), (8, 2), (0, 3), (7, 3), (14, 3), (2, 6), (6, 6), (8, 6),  (12, 6), (3, 7),
                 (11, 7),(2, 8), (6, 8), (8, 8),(12, 8),(0, 11), (7, 11),(14, 11),(6, 12),(8, 12), (3, 14), (11, 14),
                }
# fmt: on

DEFAULT = {
    'path': {
        'src_dir': str(Path(__file__).resolve().parent),
        'work_dir': '%(src_dir)s/../work',
        'log_dir': '%(src_dir)s/../work/log',
        'web_dir': '%(src_dir)s/../work/web',
    },
    'development': {'simulate_path': 'test/game01/image-{:d}.jpg', 'recording': 'False'},
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
    'video': {'warp': 'True', 'width': '976', 'height': '976', 'fps': '25', 'rotate': 'True', 'warp_coordinates': ''},
    'board': {
        'layout': 'custom2012',
        'tiles_threshold': '800',
        'min_tiles_rate': '96',
        'dynamic_threshold': 'True',
        'language': 'de',
    },
    'system': {'quit': 'shutdown', 'gitbranch': 'main'},
}


logger = logging.getLogger()


def as_bool(string: str) -> bool:
    """convert boolean string to boolean value"""
    return string.lower() in ('true', 'yes')


@dataclass
class PathConfig:
    """access to path configuration"""

    config: configparser.ConfigParser

    @property
    def src_dir(self) -> Path:
        """Get source directory"""
        return Path(self.config.get('path', 'src_dir', fallback=str(Path(__file__).resolve().parent))).resolve()

    @property
    def work_dir(self) -> Path:
        """Get working directory"""
        return Path(self.config.get('path', 'work_dir', fallback=str(self.src_dir.parent / 'work'))).resolve()

    @property
    def log_dir(self) -> Path:
        """Get log directory"""
        return Path(self.config.get('path', 'log_dir', fallback=str(self.src_dir.parent / 'work' / 'log'))).resolve()

    @property
    def web_dir(self) -> Path:
        """Get web output directory"""
        return Path(self.config.get('path', 'web_dir', fallback=str(self.src_dir.parent / 'work' / 'web'))).resolve()


@dataclass
class DevelopmentConfig:
    """access to development configuration"""

    config: configparser.ConfigParser

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


@dataclass
class VideoConfig:
    """access to video configuration"""

    config: configparser.ConfigParser

    @property
    def warp(self) -> bool:
        """Should video be warped (perspective correction)?"""
        return self.config.getboolean('video', 'warp', fallback=as_bool(DEFAULT['video']['warp']))

    @property
    def warp_coordinates(self) -> list | None:
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
        self.ini_path: Path = (Path(__file__).resolve().parent / '..' / 'work' / 'scrabble.ini').resolve()
        self.reload(ini_file=None, clean=False)
        self.is_testing: bool = False
        self.path = PathConfig(config=self.config)
        self.development = DevelopmentConfig(config=self.config)
        self.scrabble = ScrabbleConfig(config=self.config)
        self.output = OutputConfig(config=self.config)
        self.video = VideoConfig(config=self.config)
        self.board = BoardConfig(config=self.config)
        self.system = SystemConfig(config=self.config)

    def reload(self, ini_file: str | None = None, clean: bool = True) -> None:
        """reload configuration"""
        if clean:
            self.config.clear()
        self.config.read_dict(DEFAULT)
        try:
            self.ini_path = Path(ini_file) if ini_file else self.ini_path
            logger.info(f'reload {self.ini_path}')
            with self.ini_path.open(encoding='UTF-8') as config_file:
                self.config.read_file(config_file)
        except OSError as oops:
            logger.error(f'can not read INI-File {self.ini_path}: error({oops.errno}): {oops.strerror}')

    def save(self) -> None:  # pragma: no cover
        """save configuration"""
        with self.ini_path.open('w', encoding='UTF-8') as config_file:
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
