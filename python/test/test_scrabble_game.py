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
import logging.config
import os
import unittest
from time import sleep
from scrabble import MoveType

from hardware.camera_thread import Camera, CameraEnum

TEST_DIR = os.path.dirname(__file__)

logging.config.fileConfig(fname=f'{os.path.dirname(os.path.abspath(__file__))}/test_log.conf',
                          disable_existing_loggers=False)


class ScrabbleGameTestCase(unittest.TestCase):
    """Test class for some scrabble games"""

    def config_setter(self, section: str, option: str, value):
        """set scrabble config"""
        from config import config

        if value is not None:
            if section not in config.config.sections():
                config.config.add_section(section)
            config.config.set(section, option, str(value))
        else:
            config.config.remove_option(section, option)

    def print_board(self, board: dict) -> str:
        """print out scrabble board dictionary"""
        result = '  |'
        for i in range(15):
            result += f'{(i + 1):2d} '
        result += ' | '
        for i in range(15):
            result += f'{(i + 1):2d} '
        result += '\n'
        for row in range(15):
            result += f"{chr(ord('A') + row)} |"
            for col in range(15):
                if (col, row) in board:
                    result += f' {board[(col, row)][0]} '
                else:
                    result += ' . '
            result += ' | '
            for col in range(15):
                result += f' {str(board[(col, row)][1])}' if (col, row) in board else ' . '
            result += ' | \n'
        return result

    def setUp(self):
        from processing import clear_last_warp

        clear_last_warp()
        self.config_setter('output', 'ftp', False)
        self.config_setter('output', 'web', False)
        self.config_setter('development', 'recording', False)

    def test_game_06(self):
        """Test game 06"""
        from display import Display
        from scrabblewatch import ScrabbleWatch
        from state import State

        self.config_setter('video', 'warp_coordinates', None)
        # self.config_setter('video', 'warp', False)
        self.config_setter('board', 'layout', 'custom')
        display = Display()
        watch = ScrabbleWatch(display)
        cam = Camera(use_camera=CameraEnum.FILE)
        cam.stream.formatter = f'{TEST_DIR}/game06/image-{{:d}}.jpg'  # type: ignore
        cam.stream.cnt = 1  # type: ignore
        state = State(cam=cam, watch=watch)
        state.cam = cam
        state.do_new_game()
        state.game.nicknames = ('Inessa', 'Stefan')
        state.press_button('RED')                                              # green begins
        for i in range(1, 17):                                                 # odd image # => green
            cam.stream.cnt = i  # type: ignore
            if i % 2 == 1:
                state.press_button('GREEN')
            else:
                state.press_button('RED')
            if state.last_submit is not None:
                while not state.last_submit.done():  # type: ignore
                    sleep(0.1)
        self.assertEqual((270, 196), state.game.moves[-1].score)
        state.press_button('YELLOW')
        sleep(0.1)
        state.press_button('DOUBT0')                                           # valid challenge
        sleep(0.1)
        state.press_button('YELLOW')
        self.assertEqual((270, 177), state.game.moves[-1].score)
        for i in range(18, 34):                                                # odd image # => red
            cam.stream.cnt = i  # type: ignore
            if i % 2 == 0:
                state.press_button('GREEN')
            else:
                state.press_button('RED')
            if state.last_submit is not None:
                while not state.last_submit.done():  # type: ignore
                    sleep(0.1)
        self.assertEqual((438, 379), state.game.moves[-1].score)
        logging.info(state.game.nicknames)
        for move in state.game.moves:
            if move.player == 0:
                if move.type == MoveType.WITHDRAW:
                    logging.info(f'{move.move}, "Yellow", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points*-1}, {move.score[0]-move.points}, {move.score[1]}')
                    logging.info(f'{move.move}, "DOUBT0", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                elif move.type == MoveType.CHALLENGE_BONUS:
                    logging.info(f'{move.move}, "Yellow", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "DOUBT1", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Yellow", "S0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                else:
                    logging.info(f'{move.move}, "Green", "S1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
            else:
                if move.type == MoveType.WITHDRAW:
                    logging.info(f'{move.move}, "Yellow", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points*-1}, {move.score[0]}, {move.score[1]-move.points}')
                    logging.info(f'{move.move}, "DOUBT0", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                elif move.type == MoveType.CHALLENGE_BONUS:
                    logging.info(f'{move.move}, "Yellow", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "DOUBT0", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Yellow", "S1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                else:
                    logging.info(
                        f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')

    def test_game_07(self):
        """Test game 07 - hand on board; finger on tile """
        from display import Display
        from scrabblewatch import ScrabbleWatch
        from state import State

        self.config_setter('video', 'warp_coordinates', None)
        # self.config_setter('video', 'warp', False)
        self.config_setter('board', 'layout', 'custom')
        display = Display()
        watch = ScrabbleWatch(display)
        cam = Camera(use_camera=CameraEnum.FILE)
        cam.stream.formatter = f'{TEST_DIR}/game07/image-{{:d}}.jpg'  # type: ignore
        cam.stream.cnt = 1  # type: ignore
        state = State(cam=cam, watch=watch)
        state.cam = cam
        state.do_new_game()
        state.game.nicknames = ('Inessa', 'Stefan')
        state.press_button('GREEN')                                            # red begins
        for i in range(1, 19):
            cam.stream.cnt = i  # type: ignore
            if i % 2 == 0:
                state.press_button('GREEN')
            else:
                state.press_button('RED')
            if state.last_submit is not None:
                while not state.last_submit.done():  # type: ignore
                    sleep(0.1)
        self.assertEqual((197, 208), state.game.moves[-1].score)
        logging.info(state.game.nicknames)
        for move in state.game.moves:
            if move.player == 0:
                if move.type == MoveType.WITHDRAW:
                    logging.info(f'{move.move}, "Yellow", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points*-1}, {move.score[0]-move.points}, {move.score[1]}')
                    logging.info(f'{move.move}, "DOUBT0", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                elif move.type == MoveType.CHALLENGE_BONUS:
                    logging.info(f'{move.move}, "Yellow", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "DOUBT1", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Yellow", "S0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                else:
                    logging.info(f'{move.move}, "Green", "S1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
            else:
                if move.type == MoveType.WITHDRAW:
                    logging.info(f'{move.move}, "Yellow", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points*-1}, {move.score[0]}, {move.score[1]-move.points}')
                    logging.info(f'{move.move}, "DOUBT0", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                elif move.type == MoveType.CHALLENGE_BONUS:
                    logging.info(f'{move.move}, "Yellow", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "DOUBT0", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Yellow", "S1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                else:
                    logging.info(
                        f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')

    def test_game_08(self):
        """Test game 08 - hand on board"""
        from display import Display
        from scrabblewatch import ScrabbleWatch
        from state import State

        self.config_setter('video', 'warp_coordinates', None)
        # self.config_setter('video', 'warp', False)
        self.config_setter('board', 'layout', 'custom')
        display = Display()
        watch = ScrabbleWatch(display)
        cam = Camera(use_camera=CameraEnum.FILE)
        cam.stream.formatter = f'{TEST_DIR}/game08/image-{{:d}}.jpg'  # type: ignore
        cam.stream.cnt = 1  # type: ignore
        state = State(cam=cam, watch=watch)
        state.cam = cam
        state.do_new_game()
        state.game.nicknames = ('Inessa', 'Stefan')
        state.press_button('GREEN')                                            # red begins
        for i in range(1, 19):
            cam.stream.cnt = i  # type: ignore
            if i % 2 == 0:
                state.press_button('GREEN')
            else:
                state.press_button('RED')
            if state.last_submit is not None:
                while not state.last_submit.done():  # type: ignore
                    sleep(0.1)
        self.assertEqual((197, 208), state.game.moves[-1].score)
        logging.info(state.game.nicknames)
        for move in state.game.moves:
            if move.player == 0:
                if move.type == MoveType.WITHDRAW:
                    logging.info(f'{move.move}, "Yellow", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points*-1}, {move.score[0]-move.points}, {move.score[1]}')
                    logging.info(f'{move.move}, "DOUBT0", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                elif move.type == MoveType.CHALLENGE_BONUS:
                    logging.info(f'{move.move}, "Yellow", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "DOUBT1", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Yellow", "S0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                else:
                    logging.info(f'{move.move}, "Green", "S1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
            else:
                if move.type == MoveType.WITHDRAW:
                    logging.info(f'{move.move}, "Yellow", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points*-1}, {move.score[0]}, {move.score[1]-move.points}')
                    logging.info(f'{move.move}, "DOUBT0", "P0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                elif move.type == MoveType.CHALLENGE_BONUS:
                    logging.info(f'{move.move}, "Yellow", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "DOUBT0", "P1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    logging.info(f'{move.move}, "Yellow", "S1", "{move.get_coord()}", '
                                 f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                else:
                    logging.info(
                        f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')

    def test_game_12(self):
        """Test game 12"""
        from display import Display
        from scrabblewatch import ScrabbleWatch
        from state import State

        self.config_setter('video', 'warp_coordinates', None)
        self.config_setter('board', 'layout', 'custom')
        display = Display()
        watch = ScrabbleWatch(display)
        cam = Camera(use_camera=CameraEnum.FILE)
        cam.stream.formatter = f'{TEST_DIR}/game12/board-{{:02d}}.png'  # type: ignore
        cam.stream.cnt = 1  # type: ignore
        state = State(cam=cam, watch=watch)
        state.cam = cam
        state.do_new_game()
        state.game.nicknames = ('A', 'S')
        state.press_button('RED')  # green begins
        for i in range(1, 21):
            cam.stream.cnt = i  # type: ignore
            if i % 2 == 1:
                state.press_button('GREEN')
            else:
                state.press_button('RED')
            if state.last_submit is not None:
                while not state.last_submit.done():  # type: ignore
                    sleep(0.1)
        self.assertEqual(185, state.game.moves[-1].score[0])
        self.assertEqual(208, state.game.moves[-1].score[1])
        print(state.game.nicknames)
        for move in state.game.moves:
            if move.player == 0:
                if move.type == MoveType.WITHDRAW:
                    print(f'{move.move}, "Yellow", "P1", "{move.get_coord()}", '
                          f'"{move.word}", {move.points*-1}, {move.score[0]-move.points}, {move.score[1]}')
                    print(f'{move.move}, "DOUBT0", "P1", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    print(f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                elif move.type == MoveType.CHALLENGE_BONUS:
                    print(f'{move.move}, "Yellow", "P0", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    print(f'{move.move}, "DOUBT1", "P0", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    print(f'{move.move}, "Yellow", "S0", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                else:
                    print(f'{move.move}, "Green", "S1", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
            else:
                if move.type == MoveType.WITHDRAW:
                    print(f'{move.move}, "Yellow", "P0", "{move.get_coord()}", '
                          f'"{move.word}", {move.points*-1}, {move.score[0]}, {move.score[1]-move.points}')
                    print(f'{move.move}, "DOUBT0", "P0", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    print(f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                elif move.type == MoveType.CHALLENGE_BONUS:
                    print(f'{move.move}, "Yellow", "P1", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    print(f'{move.move}, "DOUBT0", "P1", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                    print(f'{move.move}, "Yellow", "S1", "{move.get_coord()}", '
                          f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')
                else:
                    print(
                        f'{move.move}, "Red", "S0", "{move.get_coord()}", '
                        f'"{move.word}", {move.points}, {move.score[0]}, {move.score[1]}')


# unit tests per commandline
if __name__ == '__main__':
    unittest.main(module='test_scrabble_game')
