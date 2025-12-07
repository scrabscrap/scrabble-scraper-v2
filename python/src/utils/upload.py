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
import logging
import queue
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

from config import config
from utils.threadpool import CommandWorker

logger = logging.getLogger()


class Upload:
    """upload files - needs configured php script on server"""

    def __init__(self):
        self.upload_queue: queue.Queue | None = None
        self.upload_worker: CommandWorker | None = None

    def get_upload_queue(self) -> queue.Queue:
        """get upload command queue"""
        if self.upload_queue is None:
            self.upload_queue = queue.Queue()
            self.upload_worker = CommandWorker(cmd_queue=self.upload_queue)
            self.upload_worker.start()
        return self.upload_queue  # type: ignore

    def upload(self, data: dict | None = None, files: dict | None = None) -> bool:
        """do upload/delete operation"""

        logger.debug(f'http: upload files data={data}, files={list(files.keys()) if files else []}')
        if data is None:
            data = {'upload': 'true'}
        if (url := upload_config.server) is not None:
            try:
                url = url if url.startswith(('http://', 'https://')) else f'https://{url}'
                url += '' if url.endswith('/bin/scrabscrap.php') else '/bin/scrabscrap.php'
                with requests.post(
                    url, data=data, files=files, timeout=50, auth=HTTPBasicAuth(upload_config.user, upload_config.password)
                ) as ret:
                    logger.info(f'upload: response {ret.status_code}')
                    if ret.status_code != 200:
                        logger.warning('upload failed: %s %s', ret.status_code, ret.text)
                        return False
                    return True
            except requests.Timeout:
                logger.exception(f'http: timeout while POST to {url}')
            except requests.ConnectionError:
                logger.exception(f'http: connection error while POST to {url}')
            except Exception:
                logger.exception(f'http: unexpected exception while POST to {url}')
            finally:
                # Ensure we close any file handles that might have been passed in
                if files:
                    for fh in files.values() if isinstance(files, dict) else files:
                        try:
                            fh.close()
                        except Exception:  # noqa: PERF203
                            logger.debug('failed to close upload file handle', exc_info=True)
        return False

    def upload_move(self, move: int) -> bool:
        """upload one move"""
        files = {
            f'image-{move}.jpg': Path(config.path.web_dir) / f'image-{move}.jpg',
            f'data-{move}.json': Path(config.path.web_dir) / f'data-{move}.json',
            'status.json': Path(config.path.web_dir) / 'status.json',
            'messages.log': Path(config.path.log_dir) / 'messages.log',
            f'image-{move}-camera.jpg': Path(config.path.web_dir) / f'image-{move}-camera.jpg',
        }
        upload_files = {}
        try:
            for key, path in files.items():
                if path.is_file():
                    upload_files[key] = path.open('rb')
            if upload_files:
                ok = self.upload(files=upload_files)
                if not ok:
                    logger.warning(f'upload_move: upload returned False for move={move} files={list(upload_files.keys())}')
                return ok
        finally:
            for f in upload_files.values():
                try:
                    f.close()
                except Exception:  # noqa: PERF203
                    logger.debug('upload_move: failed closing file handle', exc_info=True)
        return False

    def upload_status(self) -> bool:
        """upload status"""
        logger.debug('start transfer status file status.json')
        files = {
            'status.json': Path(config.path.web_dir) / 'status.json',
            'messages.log': Path(config.path.log_dir) / 'messages.log',
        }
        try:
            upload_files = {}
            for key, path in files.items():
                if path.is_file():
                    upload_files[key] = path.open('rb')
            if upload_files:
                return self.upload(files=upload_files)
        except OSError as oops:
            logger.error(f'upload I/O error({oops.errno}): {oops.strerror}')
        return False

    def delete_files(self) -> bool:
        """delete files of current game on server"""
        logger.debug('http: delete files')
        return self.upload(data={'delete': 'true'})

    def zip_files(self, fname: str) -> bool:
        """create zip of current game on server"""
        logger.debug('http: zip files on server')
        return self.upload(data={'zip': 'true', 'fname': fname})


class UploadConfig:
    """read upload configuration"""

    SECTION: str = 'upload'
    INIFILE: str = 'upload-secret.ini'

    def __init__(self) -> None:
        self.parser = configparser.ConfigParser()
        self.reload()
        self.config = self.parser[self.SECTION]

    def reload(self) -> None:
        """reload configuration"""
        self.parser = configparser.ConfigParser()
        ini_path = Path(config.path.work_dir) / self.INIFILE
        try:
            with ini_path.open(encoding='utf-8') as config_file:
                self.parser.read_file(config_file)
        except OSError as oops:
            logger.exception(f'read ini-file failed {oops} (path={ini_path})')
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
    def server(self) -> str | None:
        """get server url"""
        return self.config.get('server', fallback=None)  # type: ignore[return-value]

    @server.setter
    def server(self, value: str):
        """set server url"""
        self.config['server'] = value

    @property
    def user(self) -> str:
        """get user name"""
        return self.config.get('user', fallback='')

    @user.setter
    def user(self, value: str):
        """set user name"""
        self.config['user'] = value

    @property
    def password(self) -> str:
        """get password"""
        return self.config.get('password', fallback='')

    @password.setter
    def password(self, value: str):
        """set password"""
        self.config['password'] = value


upload_config = UploadConfig()
upload: Upload = Upload()
