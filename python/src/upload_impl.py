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
import ftplib
import logging
from concurrent import futures
from concurrent.futures import Future
from pathlib import Path
from typing import Protocol

import requests
from requests.auth import HTTPBasicAuth

from config import config

last_future: Future | None = None


class Upload(Protocol):
    """upload files"""

    def waitfor_future(self, waitfor: Future | None):
        """wait for future and skips wait if waitfor is None"""
        if waitfor is not None:
            _, not_done = futures.wait({waitfor})
            if len(not_done) != 0:
                logging.error(f'error while waiting for future - lenght of not_done: {len(not_done)}')

    def upload(self, data: dict | None = None, files: dict | None = None) -> bool:
        """do upload/delete operation"""
        return False

    def upload_move(self, waitfor: Future | None, move: int) -> bool:
        """upload one move"""
        files = {
            f'image-{move}.jpg': Path(config.path.web_dir) / f'image-{move}.jpg',
            f'data-{move}.json': Path(config.path.web_dir) / f'data-{move}.json',
            'status.json': Path(config.path.web_dir) / 'status.json',
            'messages.log': Path(config.path.log_dir) / 'messages.log',
            f'image-{move}-camera.jpg': Path(config.path.web_dir) / f'image-{move}-camera.jpg',
        }

        self.waitfor_future(waitfor)
        try:
            upload_files = {}
            for key, path in files.items():
                if path.is_file():
                    upload_files[key] = path.open('rb')
            if upload_files:
                return self.upload(files=upload_files)
        except OSError as oops:
            logging.error(f'upload I/O error({oops.errno}): {oops.strerror}')
        return False

    def upload_status(self, waitfor: Future | None) -> bool:
        """upload status"""
        logging.debug('start transfer status file status.json')
        files = {
            'status.json': Path(config.path.web_dir) / 'status.json',
            'messages.log': Path(config.path.log_dir) / 'messages.log',
        }
        self.waitfor_future(waitfor)
        try:
            upload_files = {}
            for key, path in files.items():
                if path.is_file():
                    upload_files[key] = path.open('rb')
            if upload_files:
                return self.upload(files=upload_files)
        except OSError as oops:
            logging.error(f'upload I/O error({oops.errno}): {oops.strerror}')
        return False

    def delete_files(self, waitfor: Future | None) -> bool:
        """cleanup uploaded files"""
        self.waitfor_future(waitfor)
        return False

    def zip_files(self, waitfor: Future | None, filename: str | None = None) -> bool:
        """zip uploaded files"""
        self.waitfor_future(waitfor)
        return False


class UploadHttp(Upload):  # pragma: no cover
    """http implementation"""

    def upload(self, data: dict | None = None, files: dict | None = None) -> bool:
        """do upload/delete operation"""

        logging.debug(f'http: upload files {list(files.keys())}' if files else 'http: no files to upload')
        if data is None:
            data = {'upload': 'true'}
        if (url := upload_config.server) is not None:
            try:
                url = url if url.startswith(('http://', 'https://')) else f'https://{url}'
                url += '' if url.endswith('/bin/scrabscrap.php') else '/bin/scrabscrap.php'
                ret = requests.post(
                    url, data=data, files=files, timeout=50, auth=HTTPBasicAuth(upload_config.user, upload_config.password)
                )
                return ret.status_code == 200
            except requests.Timeout:
                logging.error(f'http: error timeout url={url}')
            except requests.ConnectionError:
                logging.error(f'http: error connection error url={url}')
        return False

    def delete_files(self, waitfor: Future | None) -> bool:
        logging.debug('http: delete files')
        self.waitfor_future(waitfor)
        return self.upload(data={'delete': 'true'})

    def zip_files(self, waitfor: Future | None, filename: str | None = None) -> bool:
        logging.debug('http: zip files on server')
        self.waitfor_future(waitfor)
        return self.upload(data={'zip': 'true'})


class UploadFtp(Upload):  # pragma: no cover
    """ftp implementation"""

    def upload(self, data: dict | None = None, files: dict | None = None) -> bool:
        """do upload/delete operation"""
        if (url := upload_config.server) is not None and files is not None:
            try:
                with ftplib.FTP_TLS(url, upload_config.user, upload_config.password) as session:
                    for key, fname in files.items():
                        with Path(fname).open('rb') as file:
                            session.storbinary(f'STOR {key}', file)  # send the file
                return True
            except OSError as oops:
                logging.error(f'ftp: I/O error({oops.errno}): {oops.strerror}')
        return False

    def delete_files(self, waitfor: Future | None) -> bool:
        """cleanup uploaded files"""
        self.waitfor_future(waitfor)
        if (url := upload_config.server) is not None:
            try:
                logging.debug('ftp: delete files')
                with ftplib.FTP_TLS(url, upload_config.user, upload_config.password) as session:
                    files = session.nlst()
                    for filename in files:
                        for prefix in ['image', 'data']:
                            if filename.startswith(prefix):
                                session.delete(filename)
                logging.info('ftp: end of delete')
                return True
            except OSError as oops:
                logging.error(f'ftp: I/O error({oops.errno}): {oops.strerror}')
        return False

    def zip_files(self, waitfor: Future | None, filename: str | None = None) -> bool:
        """zip uploaded files"""
        self.waitfor_future(waitfor)
        logging.debug('ftp: upload zip file')
        try:
            files = {f'{filename}.zip': (config.path.web_dir / f'{filename}.zip').open('rb')}  # pylint: disable=R1732
            return self.upload(files=files)
        except OSError as oops:
            logging.error(f'http: I/O error({oops.errno}): {oops.strerror}')
        return False


class UploadConfig:
    """read upload configuration"""

    SECTION: str = 'upload'
    INIFILE: str = 'upload-secret.ini'

    def __init__(self) -> None:
        self.parser = configparser.ConfigParser()
        self.reload()
        self.config = self.parser[self.SECTION]

    def reload(self, clean=True) -> None:
        """reload configuration"""
        if clean:
            self.parser = configparser.ConfigParser()
        try:
            ini_path = Path(config.path.work_dir) / self.INIFILE
            with ini_path.open(encoding='utf-8') as config_file:
                self.parser.read_file(config_file)
        except OSError as oops:
            logging.error(f'read ini-file: I/O error({oops.errno}): {oops.strerror}')
        if self.SECTION not in self.parser.sections():
            self.parser.add_section(self.SECTION)
            self.store()

    def store(self) -> bool:
        """save configuration to file"""
        ini_path = Path(config.path.work_dir) / self.INIFILE
        with ini_path.open('w', encoding='UTF-8') as config_file:
            self.parser.write(config_file)
        return True

    @property
    def server(self) -> str:
        """get server url"""
        return self.config.get('server', fallback=None)  # type: ignore[return-value]

    @server.setter
    def server(self, value: str):
        """set server url in memory - to persists use store()"""
        self.config['server'] = value

    @property
    def user(self) -> str:
        """get user name"""
        return self.config.get('user', fallback='')  # type: ignore[return-value]

    @user.setter
    def user(self, value: str):
        """set user name in memory - to persists use store()"""
        self.config['user'] = value

    @property
    def password(self) -> str:
        """get password"""
        return self.config.get('password', fallback='')  # type: ignore[return-value]

    @password.setter
    def password(self, value: str):
        """set password in memory - to persists use store()"""
        self.config['password'] = value


upload_config = UploadConfig()
