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
import logging

import requests
from requests.auth import HTTPBasicAuth

from config import config
from upload_config import UploadConfig


class UploadHttp:
    """ http implementation """

    @classmethod
    def upload_move(cls, move: int) -> bool:
        """ upload move to http server """
        if (url := UploadConfig().server) is not None:
            logging.debug(f'http: upload_move {move}')

            try:
                logging.debug('http: start transfer move files')
                data = {'upload': 'true'}
                # R1732: consider-using-with
                toupload = {f'image-{move}.jpg': open(f'{config.web_dir}/image-{move}.jpg', 'rb'),  # pylint: disable=R1732
                            f'data-{move}.json': open(f'{config.web_dir}/data-{move}.json', 'rb'),  # pylint: disable=R1732
                            'status.json': open(f'{config.web_dir}/status.json', 'rb')  # pylint: disable=R1732
                            }
                try:
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    ret = requests.post(url, data=data, files=toupload, timeout=5,
                                        auth=HTTPBasicAuth(UploadConfig().user, UploadConfig().password))
                    logging.debug(ret.text)
                    logging.info('http: end of transfer')
                    if ret.status_code == 200:
                        return True
                except requests.Timeout:
                    logging.warning('http: error timeout')
                except requests.ConnectionError:
                    logging.warning('http: error connection error')
            except IOError as oops:
                logging.error(f'http: I/O error({oops.errno}): {oops.strerror}')
        return False

    @classmethod
    def upload_status(cls) -> bool:
        """ upload status to http server """
        if (url := UploadConfig().server) is not None:
            try:
                logging.debug('http: start transfer status.json files')
                data = {'upload': 'true'}
                toupload = {'status.json': open(f'{config.web_dir}/status.json', 'rb')}  # pylint: disable=consider-using-with

                try:
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    ret = requests.post(url, data=data, files=toupload, timeout=5,
                                        auth=HTTPBasicAuth(UploadConfig().user, UploadConfig().password))
                    logging.debug(ret.text)
                    logging.info('http: end of transfer')
                    if ret.status_code == 200:
                        return True
                except requests.Timeout:
                    logging.warning('http: error timeout')
                except requests.ConnectionError:
                    logging.warning('http: error connection error')
            except IOError as oops:
                logging.error(f'http: I/O error({oops.errno}): {oops.strerror}')
        return False

    @classmethod
    def upload_game(cls, filename: str) -> bool:
        """ upload a zpped game file to http """
        if (url := UploadConfig().server) is not None:
            try:
                logging.debug('http: start transfer zip file')
                data = {'upload': 'true'}
                # R1732: consider-using-with
                toupload = {f'{filename}.zip': open(f'{config.web_dir}/{filename}.zip', 'rb')}  # pylint: disable=R1732
                try:
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    ret = requests.post(url, data=data, files=toupload, timeout=5,
                                        auth=HTTPBasicAuth(UploadConfig().user, UploadConfig().password))
                    logging.debug(ret.text)
                    logging.info('http: end of transfer')
                    if ret.status_code == 200:
                        return True
                except requests.Timeout:
                    logging.warning('http: error timeout')
                except requests.ConnectionError:
                    logging.warning('http: error connection error')
            except IOError as oops:
                logging.error(f'http: I/O error({oops.errno}): {oops.strerror}')
        return False

    @classmethod
    def delete_files(cls) -> bool:
        """ delete files on http server """
        if (url := UploadConfig().server) is not None:
            try:
                logging.debug('http: delete files')
                data = {'delete': 'true'}

                try:
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    ret = requests.post(url, data=data, timeout=5, auth=HTTPBasicAuth(
                        UploadConfig().user, UploadConfig().password))
                    logging.debug(ret.text)
                    logging.info('http: end of delete')
                    if ret.status_code == 200:
                        return True
                except requests.Timeout:
                    logging.warning('http: error timeout')
                except requests.ConnectionError:
                    logging.warning('http: error connection error')
            except IOError as oops:
                logging.error(f'http: I/O error({oops.errno}): {oops.strerror}')
        return False
