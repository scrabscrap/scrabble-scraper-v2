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
import logging

from config import config
from util import Singleton


class UploadConfig(metaclass=Singleton):
    """ read upload configuration """
    SECTION = 'upload'

    def __init__(self) -> None:
        self.config = configparser.ConfigParser()
        self.reload(clean=False)

    def reload(self, clean=True) -> None:
        """ reload configuration """
        if clean:
            self.config = configparser.ConfigParser()
        try:
            with open(f'{config.work_dir}/upload-secret.ini', 'r', encoding="UTF-8") as config_file:
                self.config.read_file(config_file)
        except IOError as oops:
            logging.error(f'read ini-file: I/O error({oops.errno}): {oops.strerror}')

    def store(self) -> bool:
        """ save configuration to file """
        with open(f'{config.work_dir}/upload-secret.ini', 'w', encoding="UTF-8") as config_file:
            self.config.write(config_file)
        return True

    @property
    def server(self) -> str:
        """ get server url """
        return self.config.get(self.SECTION, 'server', fallback='')

    @server.setter
    def server(self, value: str):
        """ set server url in memory - to persists use store() """
        if self.SECTION not in self.config.sections():
            self.config.add_section(self.SECTION)
        self.config.set(self.SECTION, 'server', str(value))

    @property
    def user(self) -> str:
        """ get user name """
        return self.config.get(self.SECTION, 'user', fallback='')

    @user.setter
    def user(self, value: str):
        """ set user name in memory - to persists use store()"""
        if self.SECTION not in self.config.sections():
            self.config.add_section(self.SECTION)
        self.config.set(self.SECTION, 'user', str(value))

    @property
    def password(self) -> str:
        """ get password """
        return self.config.get(self.SECTION, 'password', fallback='')

    @password.setter
    def password(self, value: str):
        """ set password in memory - to persists use store()"""
        if self.SECTION not in self.config.sections():
            self.config.add_section(self.SECTION)
        self.config.set(self.SECTION, 'password', str(value))
