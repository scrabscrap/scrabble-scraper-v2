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
    _instances = {}  # type: ignore # storage for singleton classes

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls)\
                .__call__(*args, **kwargs)
        return cls._instances[cls]


def runtime_measure(func):
    """perform runtime measure"""

    @functools.wraps(func)
    def do_runtime_measure(*args, **kwargs):
        start = time.perf_counter()
        ret = func(*args, **kwargs)
        end = time.perf_counter()
        logging.debug(f'{func.__name__} took {end-start} sec(s).')
        return ret

    return do_runtime_measure


def trace(func):
    """perform method trace"""

    @functools.wraps(func)
    def do_trace(*args, **kwargs):
        try:
            logging.debug(f'entering {func.__name__}')
            return func(*args, **kwargs)
        except Exception:  # type: ignore
            logging.debug(f'exception in {func.__name__}')
            raise
        finally:
            logging.debug(f'leaving {func.__name__}')

    return do_trace


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
    logger_dict = {'': root, **root.manager.loggerDict}  # type: ignore
    for keys, values in logger_dict.items():
        if loggers is not None and keys not in loggers:
            continue
        try:
            for handler in values.handlers:
                if isinstance(handler, BaseRotatingHandler) and handler not in handlers:
                    handlers.append(handler)
        except AttributeError:
            pass
    for handler in handlers:
        handler.doRollover()  # type: ignore # flase positive on mypy


def get_ipv4() -> str:
    """try to get an ipv4 adress"""
    import socket

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server_socket.connect(('10.255.255.255', 1))
        ip_addr = server_socket.getsockname()[0]
    except socket.error:
        ip_addr = '127.0.0.1'
    finally:
        server_socket.close()
    return ip_addr
