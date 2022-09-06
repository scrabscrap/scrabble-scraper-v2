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
import functools
import logging
import time
from logging.handlers import BaseRotatingHandler
from typing import Union

# def onexit(f):
#     # see: https://peps.python.org/pep-0318/#examples
#     import atexit
#     atexit.register(f)
#     return f


class Singleton(type):
    """ Metaclass that creates a Singleton base type when called. """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls)\
                .__call__(*args, **kwargs)
        return cls._instances[cls]


def runtime_measure(fn):
    @functools.wraps(fn)
    def runtime_measure(*args, **kwargs):
        start = time.time()
        ret = fn(*args, **kwargs)
        end = time.time()
        logging.debug(f'{fn.__name__} took {end-start} sec(s).')
        return ret

    return runtime_measure


def trace(fn):
    @functools.wraps(fn)
    def trace(*args, **kwargs):
        try:
            logging.debug(f'entering {fn.__name__}')
            return fn(*args, **kwargs)
        except Exception:  # type: ignore
            logging.debug(f'exception in {fn.__name__}')
            raise
        finally:
            logging.debug(f'leaving {fn.__name__}')

    return trace


def rotate_logs(loggers: Union[str, list] = None, delimiter: str = ','):  # type: ignore
    """Rotate logs.

    Args:
        loggers: List of logger names as list object or as string,
            separated by `delimiter`.

        delimiter: Separator for logger names, if `loggers` is :obj:`str`.
            Defaults to ``,`` (comma).

    """
    # Convert loggers to list.
    if isinstance(loggers, str):
        loggers = [t.strip() for t in loggers.split(delimiter)]
    handlers = []
    root = logging.getLogger()
    # Include root logger in dict.
    ld = {'': root, **root.manager.loggerDict}
    for k, v in ld.items():
        if loggers is not None and k not in loggers:
            continue
        try:
            for h in v.handlers:
                if (isinstance(h, BaseRotatingHandler) and h not in handlers):
                    handlers.append(h)
        except AttributeError:
            pass
    for h in handlers:
        h.doRollover()
