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
# pylint: disable=duplicate-code

import logging
from typing import Optional

import cv2
import numpy as np

from customboard import CustomBoard
from util import TImage


class Custom2012Board(CustomBoard):
    """Implementation custom 2012 scrabble board analysis"""

    # layout 2012
    # TLETTER = [[95, 80, 20], [130, 255, 255]]                                # 205 => 102 (-7, +28)
    # DLETTER = [[95, 60, 20], [130, 255, 255]]
    # TWORD = [[145, 80, 10], [180, 255, 255], [0, 80, 10], [10, 255, 255]]    # 360 => 180 (-35, +10)
    # DWORD = [[145, 50, 10], [180, 255, 255], [0, 80, 10], [10, 255, 255]]
    # FIELD = [[30, 85, 20], [90, 255, 255]]                                   # 140 => 70  (-40, + 20)

    @classmethod
    def filter_image(cls, _image: TImage) -> tuple[Optional[TImage], set]:  # pylint: disable=too-many-locals
        def autocontrast(image: TImage) -> TImage:
            from PIL import Image, ImageOps

            pil_img: Image.Image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            pil_img = ImageOps.autocontrast(pil_img)
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        image = _image
        warped_hsv = cv2.cvtColor(_image, cv2.COLOR_BGR2HSV)
        (_, _, average_v) = cv2.mean(warped_hsv)[:3]
        if average_v < 90:
            logging.warning(f'>>>  {average_v=} start autocontrast')
            image = autocontrast(image=image)

        return CustomBoard.filter_image(image)


# test and debug
def main():  # pylint: disable=too-many-locals
    """main function for test and debug"""
    import sys

    from numpy import hstack, vstack

    from config import config
    from game_board.board import GRID_H, GRID_W, OFFSET

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        force=True,
        format='%(asctime)s [%(levelname)-1.1s] %(funcName)-15s: %(message)s',
    )

    files = [
        'test/game01/image-21.jpg',
        'test/game02/image-21.jpg',
        'test/game03/image-21.jpg',
        'test/game04/image-21.jpg',
        'test/game05/image-21.jpg',
        'test/game06/image-21.jpg',
        'test/game06/image-24.jpg',
        'test/game12/board-19.png',
        'test/game13/23113-180628-30.jpg',
        'test/game14/image-30.jpg',
        'test/game2023DM-01/image-24.jpg',
        'test/board2012/err-03.png',
        'test/board2012/err-11.png',
        'test/board2012/err-dark-01.jpg',
        'test/board2012/err-dark-02.jpg',
        'test/board2012/err-dark-03.jpg',
        'test/board2012/err-dark-04.jpg',
    ]

    config.config.set('development', 'recording', 'True')
    logging.error('#####################################################')
    logging.error('# err-11.jpg, err-dark-*.jpg recognised with errors #')
    logging.error('#####################################################')
    for fn in files:
        image = cv2.imread(fn)
        warped = CustomBoard.warp(image)

        result, tiles_candidates = CustomBoard.filter_image(_image=warped.copy())
        mask = np.zeros(warped.shape[:2], dtype='uint8')
        for col, row in tiles_candidates:
            px_col = int(OFFSET + (row * GRID_H))
            px_row = int(OFFSET + (col * GRID_W))
            mask[px_col : px_col + GRID_H, px_row : px_row + GRID_W] = 255

        masked = cv2.bitwise_and(warped, warped, mask=mask)
        blend = cv2.addWeighted(warped, 0.3, masked, 0.7, 0.0)
        result1 = hstack([warped, blend, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)])
        result2 = cv2.cvtColor(cv2.resize(result, (2400, 340)), cv2.COLOR_GRAY2BGR)
        result = vstack([result1, result2])

        cv2.imshow(f'{fn}', result)
        cv2.waitKey()
        cv2.destroyWindow(f'{fn}')


if __name__ == '__main__':
    main()
