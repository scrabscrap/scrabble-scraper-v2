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
from config import config
from upload_ftp import UploadFtp
from upload_http import UploadHttp
from util import Static


class Upload(Static):
    """ abstract implementation upload """

    @classmethod
    def upload_move(cls, move: int) -> bool:
        """ upload move to ftp server """
        if config.upload_server:
            if 'ftp' == config.upload_modus:
                return UploadFtp.upload_move(move=move)
            return UploadHttp.upload_move(move=move)
        return False

    @classmethod
    def upload_status(cls) -> bool:
        """ upload status to ftp server """
        if config.upload_server:
            if 'ftp' == config.upload_modus:
                return UploadFtp.upload_status()
            return UploadHttp.upload_status()
        return False

    @classmethod
    def upload_game(cls, filename: str) -> bool:
        """ upload a zpped game file to ftp """
        if config.upload_server:
            if 'ftp' == config.upload_modus:
                return UploadFtp.upload_game(filename=filename)
            return UploadHttp.upload_game(filename=filename)
        return False

    @classmethod
    def delete_files(cls) -> bool:
        """ delete files on ftp server """
        if config.upload_server:
            if 'ftp' == config.upload_modus:
                return UploadFtp.delete_files()
            return UploadHttp.delete_files()
        return False
