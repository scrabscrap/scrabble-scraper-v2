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
import ftplib
import logging

from config import Config
from upload_config import UploadConfig
from util import Static


class UploadFtp(Static):
    """ ftp implementation """

    @classmethod
    def upload_move(cls, move: int) -> bool:
        """ upload move to ftp server """
        if (url := UploadConfig.server()) is not None:
            logging.debug(f'ftp: upload_move {move}')
            try:
                logging.debug('ftp: start transfer move files')
                with ftplib.FTP(url, UploadConfig.user(), UploadConfig.password()) as session:
                    with open(f'{Config.web_dir()}/image-{move}.jpg', 'rb') as file:
                        session.storbinary(f'STOR image-{move}.jpg', file)  # send the file
                    with open(f'{Config.web_dir()}/data-{move}.json', 'rb') as file:
                        session.storbinary(f'STOR data-{move}.json', file)  # send the file
                    with open(f'{Config.web_dir()}/data-{move}.json', 'rb') as file:
                        session.storbinary('STOR status.json', file)  # send the file
                logging.info('ftp: end of transfer')
                return True
            except IOError as oops:
                logging.error(f'ftp: I/O error({oops.errno}): {oops.strerror}')
        return False

    @classmethod
    def upload_status(cls) -> bool:
        """ upload status to ftp server """
        if (url := UploadConfig.server()) is not None:
            logging.debug('ftp: upload status.json')
            try:
                logging.debug('ftp: start transfer move files')
                with ftplib.FTP(url, UploadConfig.user(), UploadConfig.password()) as session:
                    with open(f'{Config.web_dir()}/status.json', 'rb') as file:
                        session.storbinary('STOR status.json', file)  # send the file
                logging.info('ftp: end of transfer')
                return True
            except IOError as oops:
                logging.error(f'ftp: I/O error({oops.errno}): {oops.strerror}')
        return False

    @classmethod
    def upload_game(cls, filename: str) -> bool:
        """ upload a zpped game file to ftp """
        if (url := UploadConfig.server()) is not None:
            logging.debug(f'ftp: upload_game {filename}')
            try:
                logging.debug('ftp: start transfer zip file')
                with ftplib.FTP(url, UploadConfig.user(), UploadConfig.password()) as session:
                    with open(f'{Config.web_dir()}/{filename}.zip', 'rb') as file:
                        session.storbinary(f'STOR {filename}.zip', file)  # send the file
                logging.info(f'ftp: end of upload {filename} to ftp-server')
                return True
            except IOError as oops:
                logging.error(f'ftp: I/O error({oops.errno}): {oops.strerror}')
        return False

    @classmethod
    def delete_files(cls) -> bool:
        """ delete files on ftp server """
        if (url := UploadConfig.server()) is not None:
            logging.debug('ftp: delete files')
            try:
                logging.debug('ftp: delete files')
                with ftplib.FTP(url, UploadConfig.user(), UploadConfig.password()) as session:
                    files = session.nlst()
                    for filename in files:
                        for prefix in ['image', 'data']:
                            if filename.startswith(prefix):
                                session.delete(filename)
                logging.info('ftp: end of delete')
                return True
            except IOError as oops:
                logging.error(f'ftp: I/O error({oops.errno}): {oops.strerror}')
        return False
