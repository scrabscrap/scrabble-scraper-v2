"""
 This file is part of the scrabble-scraper distribution (https://github.com/scrabscrap/scrabble-scraper)
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

from util import Singleton


class Config(metaclass=Singleton):

    def __init__(self) -> None:
        self.config = configparser.ConfigParser()
        try:
            self.config['path'] = {}
            self.config['path']['src_dir'] = os.path.dirname(__file__) or '.'
            with open(f'{self.WORK_DIR}/scrabble.ini', 'r') as config_file:
                self.config.read_file(config_file)
        except Exception as e:
            logging.exception(f'can not read INI-File {e}')

    def reload(self) -> None:
        self.__init__()

    def save(self) -> None:
        with open(f'{self.WORK_DIR}/scrabble.ini', 'w') as config_file:
            val = self.config['path']['src_dir']
            if val == (os.path.dirname(__file__) or '.'):
                self.config.remove_option('path', 'src_dir')
                self.config.write(config_file)
                self.config['path']['src_dir'] = val
            else:
                self.config.write(config_file)

    def config_as_dict(self) -> dict:
        return {s: dict(self.config.items(s)) for s in self.config.sections()}

    @property
    def SRC_DIR(self) -> str:
        return self.config.get('path', 'src_dir', fallback=os.path.dirname(__file__) or '.')

    @property
    def WORK_DIR(self) -> str:
        return self.config.get('path', 'work_dir', fallback=f'{self.SRC_DIR}/../work')

    @property
    def LOG_DIR(self) -> str:
        return self.config.get('path', 'log_dir', fallback=f'{self.SRC_DIR}/../work/log')

    @property
    def WEB_DIR(self) -> str:
        return self.config.get('path', 'web_dir', fallback=f'{self.SRC_DIR}/../work/web')

    @property
    def SIMULATE(self) -> bool:
        return self.config.getboolean('development', 'simulate', fallback=False)

    @property
    def SIMULATE_PATH(self) -> str:
        return self.config.get('development', 'simulate_path', fallback=self.WORK_DIR + '/simulate/image-{:d}.jpg')

    @property
    def MALUS_DOUBT(self) -> int:
        return self.config.getint('scrabble', 'malus_doubt', fallback=10)

    @property
    def MAX_TIME(self) -> int:
        return self.config.getint('scrabble', 'max_time', fallback=1800)

    @property
    def MIN_TIME(self) -> int:
        return self.config.getint('scrabble', 'min_time', fallback=-300)

    @property
    def DOUBT_TIMEOUT(self) -> int:
        return self.config.getint('scrabble', 'doubt_timeout', fallback=20)

    @property
    def DOUBT_WARN(self) -> int:
        return self.config.getint('scrabble', 'doubt_warn', fallback=15)

    @property
    def SCREEN(self) -> bool:
        return self.SIMULATE or self.config.getboolean('output', 'screen', fallback=False)

    @property
    def WRITE_WEB(self) -> bool:
        return self.config.getboolean('output', 'web', fallback=True)

    @property
    def FTP(self) -> bool:
        return self.config.getboolean('output', 'ftp', fallback=False)

    @property
    def KEYBOARD(self) -> bool:
        return self.SIMULATE or self.config.getboolean('input', 'keyboard', fallback=True)

    @property
    def HOLD1(self) -> int:
        return self.config.getint('button', 'hold1', fallback=3)

    @property
    def WARP(self) -> bool:
        return self.config.getboolean('video', 'warp', fallback=True)

    @property
    def WARP_COORDINATES(self) -> Optional[list]:
        warp_coordinates_as_string = self.config.get('video', 'warp_coordinates', fallback=None)
        if warp_coordinates_as_string is None or len(warp_coordinates_as_string) <= 0:
            return None
        else:
            return json.loads(warp_coordinates_as_string)

    @property
    def IM_WIDTH(self) -> int:
        return self.config.getint('video', 'width', fallback=992)

    @property
    def IM_HEIGHT(self) -> int:
        return self.config.getint('video', 'height', fallback=976)

    @property
    def FPS(self) -> int:
        return self.config.getint('video', 'fps', fallback=30)

    @property
    def ROTATE(self) -> bool:
        return self.config.getboolean('video', 'rotate', fallback=False)

    @property
    def BOARD_LAYOUT(self) -> str:
        return self.config.get('board', 'layout', fallback='custom').replace('"', '')

    @property
    def TILES_LANGUAGE(self) -> str:
        # use german language as default
        return self.config.get('tiles', 'language', fallback='de')

    @property
    def TILES_IMAGE_PATH(self) -> str:
        # use builtin path as default
        return self.config.get('tiles', 'image_path', fallback=f'{self.SRC_DIR}/game_board/img')

    @property
    def TILES_BAG(self) -> dict:
        # use german tiles as default
        bag_as_str = self.config.get(self.TILES_LANGUAGE, 'bag',
                                     fallback='{"A": 5, "B": 2, "C": 2, "D": 4, "E": 15, "F": 2, "G": 3, "H": 4, "I": 6, '
                                     '"J": 1, "K": 2, "L": 3, "M": 4, "N": 9, "O": 3, "P": 1, "Q": 1, "R": 6, "S": 7, '
                                     '"T": 6, "U": 6, "V": 1, "W": 1, "X": 1, "Y": 1, "Z": 1, '
                                     '"\u00c4": 1, "\u00d6": 1, "\u00dc": 1, "_": 2}')
        return json.loads(bag_as_str)

    @property
    def TILES_SCORES(self) -> dict:
        # use german tiles as default
        bag_as_str = self.config.get(self.TILES_LANGUAGE, 'scores',
                                     fallback='{"A": 1, "B": 3, "C": 4, "D": 2, "E": 1, "F": 4, "G": 2, "H": 4, "I": 1, '
                                     '"J": 8, "K": 5, "L": 1, "M": 3, "N": 1, "O": 2, "P": 3, "Q": 10, "R": 1, "S": 1, '
                                     '"T": 1, "U": 1, "V": 4, "W": 4, "X": 8, "Y": 4, "Z": 10, "_": 0}')
        return json.loads(bag_as_str)

    @property
    def SYSTEM_QUIT(self) -> str:
        return self.config.get('system', 'quit', fallback='shutdown').replace('"', '')

    @property
    def MOTION_DETECTION(self) -> str:
        return self.config.get('motion', 'detection', fallback='KNN')

    @property
    def MOTION_LEARNING_RATE(self) -> float:
        return self.config.getfloat('motion', 'learningRate', fallback=0.1)

    @property
    def MOTION_WAIT(self) -> float:
        return self.config.getfloat('motion', 'wait', fallback=0.3)

    @property
    def MOTION_AREA(self) -> int:
        return self.config.getint('motion', 'area', fallback=1500)


config = Config()
