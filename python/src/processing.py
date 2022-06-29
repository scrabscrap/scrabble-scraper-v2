import logging
import time


def move(waitfor, game, img):
    logging.debug(f'move')
    time.sleep(1.5)
    pass


def valid_challenge(waitfor, game):
    logging.debug(f'valid challenge')
    time.sleep(0.1)
    pass


def invalid_challenge(waitfor, game):
    logging.debug(f'invalid challenge')
    time.sleep(0.1)
    pass


def end_of_game(waitfor):
    logging.debug(f'end of game')
    time.sleep(1.5)
    pass
