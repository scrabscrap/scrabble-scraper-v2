
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
from config import config
from display import Display


class MockDisplay(Display):

    def stop(self) -> None:
        pass

    def show_boot(self) -> None:
        print('| Boot  |')

    def show_reset(self) -> None:
        print('| Reset |')

    def show_ready(self) -> None:
        print('| Ready |')

    def show_pause(self, player: int) -> None:
        print(f'| Pause{player}|')

    def add_malus(self, player) -> None:
        if player == 0:
            print('(-10 /    )')
        else:
            print('(    / -10)')

    def add_remove_tiles(self, player) -> None:
        if player == 0:
            print('| Entf. Zug / ')
        else:
            print('|           / Entf. Zug')

    def show_cam_err(self) -> None:
        print('| \u2620 Cam |')

    def show_ftp_err(self) -> None:
        print('| \u2620 Ftp |')

    def show_config(self) -> None:
        print('| \u270E Cfg |')

    def add_time(self, player, t1, p1, t2, p2) -> None:
        m1, s1 = divmod(abs(config.MAX_TIME - t1), 60)
        m2, s2 = divmod(abs(config.MAX_TIME - t2), 60)
        doubt1 = 'x' if player == 0 and p1 <= config.DOUBT_TIMEOUT else ' '
        doubt2 = 'x' if player == 1 and p2 <= config.DOUBT_TIMEOUT else ' '
        left = f'{doubt1} -{m1:1d}:{s1:02d} ({p1:4d})' if config.MAX_TIME - \
            t1 < 0 else f'{doubt1} {m1:02d}:{s1:02d} ({p1:4d})'
        right = f'{doubt2} -{m2:1d}:{s2:02d} ({p2:4d})' if config.MAX_TIME - \
            t2 < 0 else f'{doubt2} {m2:02d}:{s2:02d} ({p2:4d})'
        print(f'|{left} / {right}|')

    def clear_message(self, player = None) -> None:
        pass

    def clear(self) -> None:
        pass

    def show(self, player = None) -> None:
        pass
