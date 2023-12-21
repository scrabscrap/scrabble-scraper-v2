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
from typing import Optional

from util import Static


class Config(Static):  # pylint: disable=too-many-public-methods
    """ access to application configuration """
    config = configparser.ConfigParser()
    ini_path: str = ''
    is_testing = False

    # def __init__(self, ini_file=None) -> None:
    #     self.config = configparser.ConfigParser()
    #     self.reload(ini_file=ini_file, clean=False)
    #     self.is_testing = False

    @classmethod
    def reload(cls, ini_file=None, clean=True) -> None:
        """ reload configuration from file """
        if clean:
            cls.config.clear()
        try:
            cls.config['path'] = {}
            cls.config['path']['src_dir'] = os.path.dirname(__file__) or '.'
            cls.ini_path = ini_file if ini_file is not None else f'{cls.work_dir()}/scrabble.ini'
            logging.info(f'reload {cls.ini_path}')
            with open(cls.ini_path, 'r', encoding="UTF-8") as config_file:
                cls.config.read_file(config_file)
        except IOError as oops:
            logging.error(f'can not read INI-File: error({oops.errno}): {oops.strerror}')

    @classmethod
    def save(cls) -> None:
        """ save configuration to file """
        with open(cls.ini_path, 'w', encoding="UTF-8") as config_file:
            val = cls.config['path']['src_dir']
            if val == (os.path.dirname(__file__) or '.'):
                cls.config.remove_option('path', 'src_dir')
                cls.config.write(config_file)
                cls.config['path']['src_dir'] = val
            else:
                cls.config.write(config_file)

    @classmethod
    def config_as_dict(cls) -> dict:
        """ get configuration as dict """
        return {s: dict(cls.config.items(s)) for s in cls.config.sections()}

    @classmethod
    def src_dir(cls) -> str:
        """get src dir"""
        return os.path.abspath(cls.config.get('path', 'src_dir', fallback=os.path.dirname(__file__) or '.'))

    @classmethod
    def work_dir(cls) -> str:
        """get work dir"""
        return os.path.abspath(cls.config.get('path', 'work_dir', fallback=f'{cls.src_dir()}/../work'))

    @classmethod
    def log_dir(cls) -> str:
        """"get logging dir"""
        return os.path.abspath(cls.config.get('path', 'log_dir', fallback=f'{cls.src_dir()}/../work/log'))

    @classmethod
    def web_dir(cls) -> str:
        """get web folder"""
        return os.path.abspath(cls.config.get('path', 'web_dir', fallback=f'{cls.src_dir()}/../work/web'))

    @classmethod
    def simulate(cls) -> bool:
        """should scrabscrap be simuated"""
        return cls.config.getboolean('development', 'simulate', fallback=False)

    @classmethod
    def simulate_path(cls) -> str:
        """folder for the simulation pictures"""
        return cls.config.get('development', 'simulate_path', fallback=cls.src_dir() + '/../test/game01/image-{:d}.jpg')

    @classmethod
    def development_recording(cls) -> bool:
        """record images in hires and moves to disk"""
        return cls.config.getboolean('development', 'recording', fallback=False)

    @classmethod
    def tournament(cls) -> str:
        """tournament"""
        return cls.config.get('scrabble', 'tournament', fallback='SCRABBLE SCRAPER')

    @classmethod
    def malus_doubt(cls) -> int:
        """malus for wrong doubt"""
        return cls.config.getint('scrabble', 'malus_doubt', fallback=10)

    @classmethod
    def max_time(cls) -> int:
        """maximum play time"""
        return cls.config.getint('scrabble', 'max_time', fallback=1800)

    @classmethod
    def min_time(cls) -> int:
        """maximum overtime"""
        return cls.config.getint('scrabble', 'min_time', fallback=-300)

    @classmethod
    def doubt_timeout(cls) -> int:
        """how long is doubt possible"""
        return cls.config.getint('scrabble', 'doubt_timeout', fallback=20)

    @classmethod
    def scrabble_verify_moves(cls) -> int:
        """moves to look back for tiles corrections"""
        return cls.config.getint('scrabble', 'verify_moves', fallback=3)

    @classmethod
    def show_score(cls) -> bool:
        """should the display show current score """
        return cls.config.getboolean('scrabble', 'show_score', fallback=False)

    @classmethod
    def upload_server(cls) -> bool:
        """should ftp upload used"""
        return cls.config.getboolean('output', 'upload_server', fallback=False)

    @classmethod
    def upload_modus(cls) -> str:
        """should ftp upload used"""
        return cls.config.get('output', 'upload_modus', fallback='http')

    # @property
    # def keyboard(self) -> bool:
    #     """should keyboard used as input device"""
    #     return self.simulate or self.config.getboolean('input', 'keyboard', fallback=False)

    @classmethod
    def video_warp(cls) -> bool:
        """should warp performed"""
        return cls.config.getboolean('video', 'warp', fallback=True)

    @classmethod
    def video_warp_coordinates(cls) -> Optional[list]:
        """stored warp coordinates"""
        warp_coordinates_as_string = cls.config.get('video', 'warp_coordinates', fallback=None)
        if warp_coordinates_as_string is None or len(warp_coordinates_as_string) <= 0:
            return None
        return json.loads(warp_coordinates_as_string)

    @classmethod
    def video_width(cls) -> int:
        """used image width"""
        return cls.config.getint('video', 'width', fallback=912)

    @classmethod
    def video_height(cls) -> int:
        """used image height"""
        return cls.config.getint('video', 'height', fallback=912)

    @classmethod
    def video_fps(cls) -> int:
        """used fps on camera monitoring"""
        return cls.config.getint('video', 'fps', fallback=30)

    @classmethod
    def video_rotate(cls) -> bool:
        """should the images rotated by 180° """
        return cls.config.getboolean('video', 'rotate', fallback=False)

    @classmethod
    def board_layout(cls) -> str:
        """which board layout should be used"""
        return cls.config.get('board', 'layout', fallback='custom2012').replace('"', '')

    @classmethod
    def tiles_language(cls) -> str:
        """used language for the tiles"""
        # use german language as default
        return cls.config.get('tiles', 'language', fallback='de')

    @classmethod
    def tiles_image_path(cls) -> str:
        """where to find the images for the tiles"""
        # use builtin path as default
        return cls.config.get('tiles', 'image_path', fallback=f'{cls.src_dir()}/game_board/img/default')

    @classmethod
    def tiles_bag(cls) -> dict:
        """how many tiles are in the bag"""
        # use german tiles as default
        bag_as_str = cls.config.get(cls.tiles_language(), 'bag',
                                    fallback='{"A": 5, "B": 2, "C": 2, "D": 4, "E": 15, "F": 2, "G": 3, "H": 4, "I": 6, '
                                    '"J": 1, "K": 2, "L": 3, "M": 4, "N": 9, "O": 3, "P": 1, "Q": 1, "R": 6, "S": 7, '
                                    '"T": 6, "U": 6, "V": 1, "W": 1, "X": 1, "Y": 1, "Z": 1, '
                                    '"\u00c4": 1, "\u00d6": 1, "\u00dc": 1, "_": 2}')
        return json.loads(bag_as_str)

    @classmethod
    def tiles_scores(cls) -> dict:
        """"scores for the tiles"""
        # use german tiles as default
        bag_as_str = cls.config.get(cls.tiles_language(), 'scores',
                                    fallback='{"A": 1, "B": 3, "C": 4, "D": 2, "E": 1, "F": 4, "G": 2, "H": 4, "I": 1, '
                                    '"J": 8, "K": 5, "L": 1, "M": 3, "N": 1, "O": 2, "P": 3, "Q": 10, "R": 1, "S": 1, '
                                    '"T": 1, "U": 1, "V": 4, "W": 4, "X": 8, "Y": 4, "Z": 10, "_": 0}')
        return json.loads(bag_as_str)

    @classmethod
    def system_quit(cls) -> str:
        """on reboot button: should the app just stop (no reboot)"""
        return cls.config.get('system', 'quit', fallback='shutdown').replace('"', '')

    @classmethod
    def system_gitbranch(cls) -> str:
        """git tag or branch to use for updates"""
        return cls.config.get('system', 'gitbranch', fallback='main').replace('"', '')

    # @property
    # def motion_detection(self) -> str:
    #     """"which mode for motion detection is used"""
    #     return self.config.get('motion', 'detection', fallback='KNN')

    # @property
    # def motion_learning_rate(self) -> float:
    #     """motion learning rate"""
    #     return self.config.getfloat('motion', 'learningRate', fallback=0.1)

    # @property
    # def motion_wait(self) -> float:
    #     """pause between motion detections"""
    #     return self.config.getfloat('motion', 'wait', fallback=0.3)

    # @property
    # def motion_area(self) -> int:
    #     """minimum size of the motion area"""
    #     return self.config.getint('motion', 'area', fallback=1500)


Config.reload()
