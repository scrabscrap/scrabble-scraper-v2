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

from collections.abc import Callable
import functools
import logging
import time
from logging.handlers import BaseRotatingHandler
from typing import Any

import numpy as np

TWarp = np.ndarray[Any, np.dtype[np.float32]]
logger = logging.getLogger()

# def onexit(f):
#     # see: https://peps.python.org/pep-0318/#examples
#     import atexit
#     atexit.register(f)
#     return f


class Static:  # pylint: disable=too-few-public-methods
    """base class for static classes"""

    def __new__(cls):
        raise TypeError('Static classes cannot be instantiated')


def handle_exceptions(func: Callable[..., Any]):
    """
    Decorator to handle common IndexError and ValueError exceptions
    and call event_set after the function execution.
    Assumes the decorated function accepts an 'event' keyword argument.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError as err:
            logger.error(f'index error in {func.__name__} ignored: "{err}"')
        except ValueError as err:
            logger.error(f'value error in {func.__name__} ignored: "{err}"')
        return None

    return wrapper


def runtime_measure(func: Callable[..., Any]) -> Callable[..., Any]:  # pragma: no cover # currently not used
    """perform runtime measure"""

    @functools.wraps(func)
    def runtime(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        logger.info(f'{func.__name__} took {(time.perf_counter() - start):.4f} sec(s).')
        return result

    return runtime


def trace(func: Callable[..., Any]) -> Callable[..., Any]:
    """perform method trace"""

    @functools.wraps(func)
    def do_trace(*args: Any, **kwargs: Any) -> Any:
        try:
            logger.debug(f'entering {func.__qualname__}')
            return func(*args, **kwargs)
        except Exception as oops:  # pragma: no cover
            logger.exception(f'exception in {func.__name__}: {oops}')
            raise
        finally:
            logger.debug(f'leaving {func.__name__}')

    return do_trace


def rotate_logs(loggers: str | list | None = None, delimiter: str = ','):  # pragma: no cover
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
    logger_dict = {'': root, **root.manager.loggerDict}
    for keys, values in logger_dict.items():
        if loggers is not None and keys not in loggers:
            continue
        try:
            for handler in values.handlers:  # type: ignore[union-attr]
                if isinstance(handler, BaseRotatingHandler) and handler not in handlers:
                    handlers.append(handler)
        except AttributeError:
            pass
    for handler in handlers:
        handler.doRollover()  # type: ignore[attr-defined] # false positive mypy
