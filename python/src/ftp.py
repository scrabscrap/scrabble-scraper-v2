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
import ftplib
import logging
from typing import Optional

from config import config


class Ftp:
    class FtpConfig:
        def __init__(self) -> None:
            self.config = configparser.ConfigParser()
            try:
                with open(f'{config.WORK_DIR}/ftp-secret.ini', 'r') as config_file:
                    self.config.read_file(config_file)
            except Exception as e:
                logging.exception(f'can not read ftp INI-File {e}')

        def reload(self) -> None:
            self.__init__()

        @property
        def FTP_SERVER(self) -> Optional[str]:
            return self.config.get('ftp', 'ftp-server', fallback=None)

        @property
        def FTP_USER(self) -> str:
            return self.config.get('ftp', 'ftp-user', fallback='')

        @property
        def FTP_PASS(self) -> str:
            return self.config.get('ftp', 'ftp-password', fallback='')

    ftp_config = FtpConfig()

    @classmethod
    def upload_move(cls, move: int) -> bool:
        logging.debug(f'ftp: upload_move {move}')
        if cls.ftp_config.FTP_SERVER is not None:
            try:
                logging.info('ftp: start transfer move files')
                with ftplib.FTP(cls.ftp_config.FTP_SERVER, cls.ftp_config.FTP_USER, cls.ftp_config.FTP_PASS) as session:
                    with open(f'{config.WEB_PATH}image-{move}.jpg', 'rb') as file:
                        session.storbinary('STOR image-{move}.jpg', file)   # send the file
                    with open(f'{config.WEB_PATH}data-{move}.json', 'rb') as file:
                        session.storbinary('STOR data-{move}.json', file)   # send the file
                        session.storbinary('STOR status.json', file)  # send the file
                return True
            except Exception as e:
                logging.error(f'ftp: upload failure {e}')
        return False

    @classmethod
    def upload_game(cls, filename: str) -> bool:
        logging.debug(f'ftp: upload_game {filename}')
        if cls.ftp_config.FTP_SERVER is not None:
            try:
                logging.info('ftp: start transfer zip file')
                with ftplib.FTP(cls.ftp_config.FTP_SERVER, cls.ftp_config.FTP_USER, cls.ftp_config.FTP_PASS) as session:
                    with open(f'{config.WEB_PATH}{filename}.zip', 'rb') as file:
                        session.storbinary(f'STOR {filename}.zip', file)  # send the file
                logging.info(f'ftp: end of upload {filename} to ftp-server')
                return True
            except Exception as e:
                logging.error(f'ftp: upload failure {e}')
        return False

    @classmethod
    def delete_files(cls, prefix: str) -> bool:
        logging.debug(f'ftp: delete files with prefix {prefix}*')
        if cls.ftp_config.FTP_SERVER is not None:
            try:
                logging.info('ftp: delete files')
                with ftplib.FTP(cls.ftp_config.FTP_SERVER, cls.ftp_config.FTP_USER, cls.ftp_config.FTP_PASS) as session:
                    files = session.nlst()
                    for i in files:
                        if i.startswith(prefix):
                            session.delete(i)  # delete (not status.json, *.zip)
                logging.info(f'ftp: end of delete {prefix}* ')
                return True
            except Exception as e:
                logging.error(f'ftp: delete failure {e}')
        return False
