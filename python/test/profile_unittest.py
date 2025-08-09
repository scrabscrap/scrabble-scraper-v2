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
import unittest

import yappi

# unit tests per commandline
if __name__ == '__main__':
    unittest_to_profile = 'test_gamerunner'

    # classic profile
    # pr = cProfile.Profile()
    # pr.enable(builtins=False)

    yappi.start()
    unittest.main(module=unittest_to_profile, exit=False)
    logging.info(f'### end of tests ###')
    yappi.stop()

    # classic profile
    # pr.stop()
    # p = Stats(pr)

    # current_module = [sys.modules['analyzer'], sys.modules['processing']]
    # yappi.get_func_stats(filter_callback=lambda x: yappi.module_matches(x, current_module)).strip_dirs().sort(
    #     'tsub', 'desc'
    # ).print_all()
    p = yappi.convert2pstats(yappi.get_func_stats())

    print(f'\n{"=" * 40}')
    # p.strip_dirs()
    p.sort_stats('tottime')
    p.print_stats('/src/', 0.2)

    p = yappi.convert2pstats(yappi.get_func_stats())
    print(f'{"=" * 40}')
    p.sort_stats('ncalls')
    p.print_stats('/src/', 0.2)
