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
import ftplib
import logging
from typing import Optional

from config import config


class Ftp:
    """ ftp implementation """

    def __init__(self):
        pass

    class FtpConfig:
        """ read ftp configuration """

        def __init__(self) -> None:
            self.config = configparser.ConfigParser()
            self.reload(clean=False)

        def reload(self, clean=True) -> None:
            """ reload ftp configuration """
            if clean:
                self.config = configparser.ConfigParser()
            try:
                with open(f'{config.work_dir}/ftp-secret.ini', 'r', encoding="UTF-8") as config_file:
                    self.config.read_file(config_file)
            except IOError as err:
                logging.exception(f'can not read ftp INI-File {err}')

        @property
        def ftp_server(self) -> Optional[str]:
            """ get ftp server name """
            return self.config.get('ftp', 'ftp-server', fallback=None)

        @property
        def ftp_user(self) -> str:
            """ get ftp user name """
            return self.config.get('ftp', 'ftp-user', fallback='')

        @property
        def ftp_pass(self) -> str:
            """ get ftp password """
            return self.config.get('ftp', 'ftp-password', fallback='')

    ftp_config = FtpConfig()

    @classmethod
    def upload_move(cls, move: int) -> bool:
        """ upload move to ftp server """
        logging.debug(f'ftp: upload_move {move}')
        if cls.ftp_config.ftp_server is not None:
            try:
                logging.info('ftp: start transfer move files')
                with ftplib.FTP(cls.ftp_config.ftp_server, cls.ftp_config.ftp_user, cls.ftp_config.ftp_pass) as session:
                    with open(f'{config.web_dir}/image-{move}.jpg', 'rb') as file:
                        session.storbinary(f'STOR image-{move}.jpg', file)  # send the file
                    with open(f'{config.web_dir}/data-{move}.json', 'rb') as file:
                        session.storbinary(f'STOR data-{move}.json', file)  # send the file
                    with open(f'{config.web_dir}/data-{move}.json', 'rb') as file:
                        session.storbinary('STOR status.json', file)  # send the file
                logging.debug('ftp: end of transfer')
                return True
            except IOError as err:
                logging.error(f'ftp: upload failure {err}')
        return False

    @classmethod
    def upload_game(cls, filename: str) -> bool:
        """ upload a zpped game file to ftp """
        logging.debug(f'ftp: upload_game {filename}')
        if cls.ftp_config.ftp_server is not None:
            try:
                logging.info('ftp: start transfer zip file')
                with ftplib.FTP(cls.ftp_config.ftp_server, cls.ftp_config.ftp_user, cls.ftp_config.ftp_pass) as session:
                    with open(f'{config.web_dir}/{filename}.zip', 'rb') as file:
                        session.storbinary(f'STOR {filename}.zip', file)  # send the file
                logging.info(f'ftp: end of upload {filename} to ftp-server')
                return True
            except IOError as err:
                logging.error(f'ftp: upload failure {err}')
        return False

    @classmethod
    def delete_files(cls, prefix: str) -> bool:
        """ delete files on ftp server """
        logging.debug(f'ftp: delete files with prefix {prefix}*')
        if cls.ftp_config.ftp_server is not None:
            try:
                logging.info('ftp: delete files')
                with ftplib.FTP(cls.ftp_config.ftp_server, cls.ftp_config.ftp_user, cls.ftp_config.ftp_pass) as session:
                    files = session.nlst()
                    for i in files:
                        if i.startswith(prefix):
                            session.delete(i)  # delete (not status.json, *.zip)
                logging.info(f'ftp: end of delete {prefix}* ')
                return True
            except IOError as err:
                logging.error(f'ftp: delete failure {err}')
        return False
