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
import queue
import threading
from concurrent.futures import ThreadPoolExecutor


class Command:  # pylint: disable=too-few-public-methods
    """Command class for sequential execution of asynchronous tasks"""

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def execute(self):
        """run queued command"""
        self.func(*self.args, **self.kwargs)


class CommandWorker(threading.Thread):
    """Worker Thread for commands"""

    def __init__(self, cmd_queue):
        super().__init__(daemon=True, name='CommandWorker')
        self.command_queue = cmd_queue

    def run(self):
        """Run worker thread"""
        while True:
            logging.warning('CommandWorker started')
            try:
                command = self.command_queue.get()  # wait for next command
                if command is None:
                    break  # None to end worker thread
                command.execute()
            except Exception as e:  # pylint: disable=broad-exception-caught
                logging.exception(f'Exception in CommandWorker {e}')
            finally:
                self.command_queue.task_done()


command_queue: queue.Queue = queue.Queue()
worker = CommandWorker(cmd_queue=command_queue)
worker.start()

pool = ThreadPoolExecutor()
