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
from util import Static


class UploadConfig(Static):
    """ read upload configuration """
    SECTION = 'upload'
    config = configparser.ConfigParser()

    @ classmethod
    def reload(cls, clean=True) -> None:
        """ reload configuration """
        if clean:
            cls.config = configparser.ConfigParser()
        try:
            with open(f'{config.work_dir}/upload-secret.ini', 'r', encoding="UTF-8") as config_file:
                cls.config.read_file(config_file)
        except IOError as oops:
            logging.error(f'read ini-file: I/O error({oops.errno}): {oops.strerror}')

    @classmethod
    def store(cls) -> bool:
        """ save configuration to file """
        with open(f'{config.work_dir}/upload-secret.ini', 'w', encoding="UTF-8") as config_file:
            cls.config.write(config_file)
        return True

    @classmethod
    def server(cls) -> str:
        """ get server url """
        return cls.config.get(cls.SECTION, 'server', fallback='')

    @classmethod
    def set_server(cls, value: str):
        """ set server url in memory - to persists use store() """
        if cls.SECTION not in cls.config.sections():
            cls.config.add_section(cls.SECTION)
        cls.config.set(cls.SECTION, 'server', str(value))

    @classmethod
    def user(cls) -> str:
        """ get user name """
        return cls.config.get(cls.SECTION, 'user', fallback='')

    @classmethod
    def set_user(cls, value: str):
        """ set user name in memory - to persists use store()"""
        if cls.SECTION not in cls.config.sections():
            cls.config.add_section(cls.SECTION)
        cls.config.set(cls.SECTION, 'user', str(value))

    @classmethod
    def password(cls) -> str:
        """ get password """
        return cls.config.get(cls.SECTION, 'password', fallback='')

    @classmethod
    def set_password(cls, value: str):
        """ set password in memory - to persists use store()"""
        if cls.SECTION not in cls.config.sections():
            cls.config.add_section(cls.SECTION)
        cls.config.set(cls.SECTION, 'password', str(value))


UploadConfig.reload()
