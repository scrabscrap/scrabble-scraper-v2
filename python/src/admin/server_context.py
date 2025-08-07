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

import platform
from dataclasses import dataclass


@dataclass(kw_only=True)
class AdminServerContext:
    """admin server context"""

    flask_shutdown_blocked = False
    scrabscrap_version = ''
    simulator = False
    tailscale = False
    local_webapp = False
    machine = platform.machine()
    server: object = None


ctx = AdminServerContext()
