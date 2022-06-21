
import logging

from abc import abstractmethod


class Display:

    @abstractmethod
    def show_boot(self) -> None:
        logging.debug('add boot')
        pass

    @abstractmethod
    def show_reset(self) -> None:
        logging.debug('add reset')
        pass

    @abstractmethod
    def show_ready(self) -> None:
        logging.debug('add ready')
        pass

    @abstractmethod
    def show_pause(self) -> None:
        logging.debug('add pause')
        pass

    @abstractmethod
    def add_malus(self, player: int) -> None:
        logging.debug(f'add malus on {player}')
        pass

    @abstractmethod
    def add_remove_tiles(self, player: int) -> None:
        logging.debug(f'add remove tiles on {player}')
        pass

    @abstractmethod
    def show_cam_err(self) -> None:
        logging.debug('add cam err')
        pass

    @abstractmethod
    def show_ftp_err(self) -> None:
        logging.debug('add cam err')
        pass

    @abstractmethod
    def show_config(self) -> None:
        logging.debug('add config')
        pass

    @abstractmethod
    def add_time(self, player: int, t1: int, p1: int, t2: int, p2: int) -> None:
        logging.debug(f'add time {t1:04d}:{p1:4d} / {t2:04d}:{p2:4d}')
        pass

    @abstractmethod
    def clear(self) -> None:
        logging.debug('clear')
        pass

    @abstractmethod
    def show(self) -> None:
        pass
