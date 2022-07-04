import logging
import unittest
from signal import pause
import time

from button import Button
from state import State

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')


class MockState():

    def __init__(self):
        self.lastpress = 0

    def do_ready(self):
        pass

    # Versuch mit Software Bounce
    # nach Release darf ein Drücken nicht innerhalb einer 0.1s 
    # erfolgen (verhindert aber schnelles Drücken!)
    # Wenn dies im State ergänzt werden soll, muss der Button
    # berücksichtigt werden
    def press_button(self, button: str) -> None:
        logging.debug(f'_ button press: {button}')
        press = time.time()
        if press < self.lastpress + 0.1:
            logging.debug(f'  {self.lastpress} {press} ignore bounce')
        pass

    def release_button(self, button: str) -> None:
        logging.debug(f'= button release: {button}\n')
        self.lastpress = time.time()
        pass


class ButtonTestCase(unittest.TestCase):

    def test_button(self):
        state = MockState()
        button_handler = Button()
        button_handler.start(state)
        print('start')
        pause()


if __name__ == '__main__':
    unittest.main()
