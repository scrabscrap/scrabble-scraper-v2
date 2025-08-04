import logging
import sys
import threading
import unittest
from unittest.mock import Mock, patch

import numpy as np

from config import config
from display import Display
from hardware import camera
from move import BoardType
from scrabblewatch import ScrabbleWatch
from state import State
from threadpool import command_queue

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, force=True, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s'
)
logger = logging.getLogger(__name__)


class BaseTestClass(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.DEBUG)  # nur Info Ausgaben
        # logging.disable(logging.INFO)  # nur Error Ausgaben
        ScrabbleWatch.display = Display()  # type: ignore
        camera.cam.read = Mock()
        camera.cam.read.return_value = np.zeros((1, 1))
        self.development_recording = config.development.recording
        config.config.set('development', 'recording', 'False')
        config.is_testing = True
        return super().setUp()

    def tearDown(self) -> None:
        config.is_testing = False
        config.config.set('development', 'recording', str(self.development_recording))
        return super().tearDown()

    def run_move(self, i: int, board: BoardType, move: dict):
        """
        Simulates a single Scrabble move.

        Mocks the image processing function to return the updated board state after the move.
        Presses the corresponding button to trigger the move logic and waits for processing if needed.
        """
        event = threading.Event()
        new_board = dict(board)
        new_board.update(move['tiles'])

        def side_effect(*args, **kwargs):
            logging.debug(f'simulate move #{i}')
            event.set()
            return (np.zeros((1, 1)), new_board)

        with patch('processing._image_processing', side_effect=side_effect) as _:
            button = move['button'].upper()
            event.clear()
            State.press_button(button)
            if button in ('RED', 'GREEN'):
                event.wait(timeout=0.1)  # wait for side_effect

    def run_data(self, start_button: str, data: list):
        """
        Runs a sequence of simulated moves for a Scrabble game.

        Initializes a new game, presses the start button, and processes each move in the provided data list.
        Waits for all commands to finish before returning.
        """
        board: BoardType = {}
        State.do_new_game()
        State.press_button(start_button.upper())
        for i, m in enumerate(data):
            self.run_move(i, board, m)
            board.update(m['tiles'])
        command_queue.join()
