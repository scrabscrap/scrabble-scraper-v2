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

import logging

from config import config
from upload_impl import Upload, UploadFtp, UploadHttp

upload_implementations = {'https': UploadHttp, 'http': UploadHttp, 'ftp': UploadFtp}

upload: Upload = upload_implementations[config.output.upload_modus]()


def update_upload_mode() -> bool:
    """set new upload mode"""
    global upload  # pylint: disable=global-statement
    mode = config.output.upload_modus.lower()
    if mode in upload_implementations:
        upload = upload_implementations[mode]()
        return True
    logging.warning(f"invalid upload mode '{mode}'")
    return False
