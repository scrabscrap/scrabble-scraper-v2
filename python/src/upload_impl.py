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
from typing import Optional, Protocol

import requests
from requests.auth import HTTPBasicAuth

from config import config


class Upload(Protocol):
    """upload files"""

    def upload_move(self, move: int) -> bool:  # type: ignore # only interface
        """upload one move"""

    def upload_status(self) -> bool:  # type: ignore # only interface
        """upload status"""

    def upload_game(self, filename: str) -> bool:  # type: ignore # only interface
        """upload complete game"""

    def delete_files(self) -> bool:  # type: ignore # only interface
        """cleanup uploaded files"""


class UploadHttp(Upload):  # pragma: no cover
    """http implementation"""

    def upload(self, data: dict, files: Optional[dict] = None) -> bool:
        """do upload/delete operation"""
        if (url := upload_config.server) is not None:
            try:
                url = url if url.startswith(('http://', 'https://')) else f'https://{url}'
                url += '' if url.endswith('/bin/scrabscrap.php') else '/bin/scrabscrap.php'
                ret = requests.post(
                    url, data=data, files=files, timeout=50, auth=HTTPBasicAuth(upload_config.user, upload_config.password)
                )
                logging.debug(f'http: status code: {ret.status_code}:{ret.reason}')
                return ret.status_code == 200
            except requests.Timeout:
                logging.error(f'http: error timeout url={url}')
            except requests.ConnectionError:
                logging.error(f'http: error connection error url={url}')
        return False

    def upload_move(self, move: int) -> bool:
        try:
            files = {
                f'image-{move}.jpg': open(f'{config.web_dir}/image-{move}.jpg', 'rb'),  # pylint: disable=R1732
                f'data-{move}.json': open(f'{config.web_dir}/data-{move}.json', 'rb'),  # pylint: disable=R1732
                'status.json': open(f'{config.web_dir}/status.json', 'rb'),  # pylint: disable=R1732
            }
            logging.debug(f'http: start transfer move files {files}')
            return self.upload(data={'upload': 'true'}, files=files)
        except IOError as oops:
            logging.error(f'http: I/O error({oops.errno}): {oops.strerror}')
        return False

    def upload_status(self) -> bool:
        logging.debug('http: start transfer status file status.json')
        try:
            files = {'status.json': open(f'{config.web_dir}/status.json', 'rb')}  # pylint: disable=consider-using-with
            return self.upload(data={'upload': 'true'}, files=files)
        except IOError as oops:
            logging.error(f'http: I/O error({oops.errno}): {oops.strerror}')
        return False

    def upload_game(self, filename: str) -> bool:
        logging.debug(f'http: start transfer game {filename}.zip')
        try:
            files = {f'{filename}.zip': open(f'{config.web_dir}/{filename}.zip', 'rb')}  # pylint: disable=R1732
            return self.upload(data={'upload': 'true'}, files=files)
        except IOError as oops:
            logging.error(f'http: I/O error({oops.errno}): {oops.strerror}')
        return False

    def delete_files(self) -> bool:
        logging.debug('http: delete files')
        return self.upload(data={'delete': 'true'})


class UploadFtp(Upload):  # pragma: no cover
    """ftp implementation"""

    def upload(self, files: dict) -> bool:
        """do upload/delete operation"""
        if (url := upload_config.server) is not None:
            try:
                with ftplib.FTP(url, upload_config.user, upload_config.password) as session:
                    for key, fname in files.items():
                        with open(fname, 'rb') as file:
                            session.storbinary(f'STOR {key}', file)  # send the file
                logging.info(f'ftp: end of transfer {files}')
                return True
            except IOError as oops:
                logging.error(f'ftp: I/O error({oops.errno}): {oops.strerror}')
        return False

    def upload_move(self, move: int) -> bool:
        files = {
            f'image-{move}.jpg': f'{config.web_dir}/image-{move}.jpg',
            f'data-{move}.json': f'{config.web_dir}/data-{move}.json',
            'status.json': f'{config.web_dir}/data-{move}.json',
        }
        logging.debug('ftp: start transfer move files {files}')
        return self.upload(files=files)

    def upload_status(self) -> bool:
        files = {'status.json': f'{config.web_dir}/status.json'}
        logging.debug(f'ftp: start transfer status file {files}')
        return self.upload(files=files)

    def upload_game(self, filename: str) -> bool:
        files = {f'{filename}.zip': f'{config.web_dir}/{filename}.zip'}
        logging.debug('ftp: start transfer game {files}')
        return self.upload(files=files)

    def delete_files(self) -> bool:
        if (url := upload_config.server) is not None:
            try:
                logging.debug('ftp: delete files')
                with ftplib.FTP(url, upload_config.user, upload_config.password) as session:
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


class UploadConfig:
    """read upload configuration"""

    SECTION = 'upload'
    INIFILE = f'{config.work_dir}/upload-secret.ini'

    def __init__(self) -> None:
        self.parser = configparser.ConfigParser()
        self.reload()
        self.config = self.parser[self.SECTION]

    def reload(self, clean=True) -> None:
        """reload configuration"""
        if clean:
            self.parser = configparser.ConfigParser()
        try:
            with open(self.INIFILE, 'r', encoding='UTF-8') as config_file:
                self.parser.read_file(config_file)
        except IOError as oops:
            logging.error(f'read ini-file: I/O error({oops.errno}): {oops.strerror}')
        if self.SECTION not in self.parser.sections():
            self.parser.add_section(self.SECTION)
            self.store()

    def store(self) -> bool:
        """save configuration to file"""
        with open(self.INIFILE, 'w', encoding='UTF-8') as config_file:
            self.parser.write(config_file)
        return True

    @property
    def server(self) -> str:
        """get server url"""
        return self.config.get('server', fallback=None)  # type: ignore

    @server.setter
    def server(self, value: str):
        """set server url in memory - to persists use store()"""
        self.config['server'] = value

    @property
    def user(self) -> str:
        """get user name"""
        return self.config.get('user', fallback='')  # type: ignore

    @user.setter
    def user(self, value: str):
        """set user name in memory - to persists use store()"""
        self.config['user'] = value

    @property
    def password(self) -> str:
        """get password"""
        return self.config.get('password', fallback='')  # type: ignore

    @password.setter
    def password(self, value: str):
        """set password in memory - to persists use store()"""
        self.config['password'] = value


upload_config = UploadConfig()
