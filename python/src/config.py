"""
 This file is part of the scrabble-scraper distribution (https://github.com/scrabscrap/scrabble-scraper)
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

import configparser
import logging
import os


class Config:

    def __init__(self) -> None:
        self.WORK_DIR = os.path.abspath(
            os.path.dirname(os.path.abspath(__file__))+"/../work")
        self.config = configparser.ConfigParser()
        try:
            with open(self.WORK_DIR + '/scrabble.ini', "r") as config_file:
                self.config.read_file(config_file)
        except Exception as e:
            logging.exception(f"can not read INI-File {e}")

    def reload(self) -> None:
        self.config = configparser.ConfigParser()
        try:
            with open(self.WORK_DIR + '/scrabble.ini', "r") as config_file:
                self.config.read_file(config_file)
        except Exception as e:
            logging.exception(f"can not read INI-File {e}")

    @property
    def SIMULATE(self) -> bool:
        return self.config.getboolean('development', 'simulate', fallback=False)

    @property
    def SIMULATE_PATH(self) -> str:
        return self.config.get('development', 'simulate_path', fallback=self.WORK_DIR+'/../work/simulate/image-{:d}.jpg')

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
    def WEB_PATH(self) -> str:
        return self.config.get('output', 'web_path', fallback=self.WORK_DIR + '/web/')

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
    def IM_WIDTH(self) -> int:
        return self.config.getint('video', 'size', fallback=972)

    @property
    def IM_HEIGHT(self) -> int:
        return self.config.getint('video', 'size', fallback=972)

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
    def SYSTEM_QUIT(self) -> str:
        return self.config.get('system', 'quit', fallback='shutdown').replace('"', '')

    @property
    def MOTION_DETECTION(self) -> str:
        return self.config.get('motion', 'detection', fallback='KNN')

    @property
    def MOTION_LEARNING_RATE(
        self) -> float: return self.config.getfloat('motion', 'learningRate', fallback=0.1)

    @property
    def MOTION_WAIT(self) -> float:
        return self.config.getfloat('motion', 'wait', fallback=0.3)

    @property
    def MOTION_AREA(self) -> int:
        return self.config.getint('motion', 'area', fallback=1500)

config = Config()
