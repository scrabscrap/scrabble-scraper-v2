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
from concurrent.futures import ThreadPoolExecutor

# the number of threads depends on the hardware (8 for RPI 3)
# reserved threads are
# 1) Camera for continuous capture
# 2) RepeatedTimer for one tick every second
# 
# additional threads will be started on demand
# *  Move, Invalid Challenge, Valid Challenge, FTP Upload
# 
# Move will additionally start 3 picture Analyse Thread
# Move, Invalid Challenge, Valid Challenge, End of Game will start FTP Upload
pool = ThreadPoolExecutor()
