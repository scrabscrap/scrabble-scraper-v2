
import logging

from abc import abstractmethod


class Display:

    @abstractmethod
    def show_boot(self):
        logging.debug('add boot')
        pass

    @abstractmethod
    def show_reset(self):
        logging.debug('add reset')
        pass

    @abstractmethod
    def show_ready(self):
        logging.debug('add ready')
        pass

    @abstractmethod
    def show_pause(self):
        logging.debug('add pause')
        pass

    @abstractmethod
    def add_malus(self, player: int):
        logging.debug(f'add malus on {player}')
        pass

    @abstractmethod
    def add_remove_tiles(self, player: int):
        logging.debug(f'add remove tiles on {player}')
        pass

    @abstractmethod
    def show_cam_err(self):
        logging.debug('add cam err')
        pass

    @abstractmethod
    def show_ftp_err(self):
        logging.debug('add cam err')
        pass

    @abstractmethod
    def show_config(self):
        logging.debug('add config')
        pass

    @abstractmethod
    def add_time(self, player: int, t1: int, p1: int, t2: int, p2: int):
        logging.debug(f'add time {t1:04d}:{p1:4d} / {t2:04d}:{p2:4d}')
        pass

    @abstractmethod
    def clear(self):
        logging.debug('clear')
        pass

    @abstractmethod
    def show(self):
        pass
