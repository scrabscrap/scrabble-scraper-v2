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
from cv2.typing import MatLike
from PIL import Image

from config import config
from customboard import CustomBoard
from game_board.board import DOUBLE_LETTER, DOUBLE_WORDS, GRID_H, GRID_W, OFFSET, TRIPLE_LETTER, TRIPLE_WORDS

# dimension board custom
# ----------------------
# overall size: 330mm x 330mm
# grid: 310mm x 310mm
# top: 10mm
# left: 10mm
# right: 10mm
# bottom: 10mm
#
# tiles
# -----
# 19mm x 19mm

# pylint: disable=duplicate-code


class Custom2012PILBoard(CustomBoard):
    """Implementation custom 2012 scrabble board analysis with Pillow (uses PIL.quantize)"""

    # Pillow uses hsv_full colors
    FIELD_COLOR = ([60, 85, 20], [125, 255, 255])

    TLETTER_COLOR = ([135, 60, 10], [185, 255, 255])
    DLETTER_COLOR = ([135, 60, 10], [185, 255, 255])

    TWORD_COLOR0 = ([0, 80, 10], [10, 255, 255])  # H: 0-10 & 145-180
    DWORD_COLOR0 = ([0, 80, 10], [10, 255, 255])  # H: 0-10 & 145-180
    TWORD_COLOR1 = ([200, 80, 10], [255, 255, 255])  # H: 0-10 & 145-180
    DWORD_COLOR1 = ([200, 80, 10], [255, 255, 255])  # H: 0-10 & 145-180

    @classmethod
    def log_color_table(cls, color_table: dict, candidates: set) -> str:
        """print color table"""
        board_size = 15
        tmp = ''
        for color in range(3):
            tmp += '  |' + ''.join(f'  {i + 1:-3d} ' for i in range(board_size)) + '\n'
            tmp += '\n'.join(
                [
                    f"""{chr(ord('A') + row)} |{''.join(f' [{color_table[(col, row)][color]:-3d}]' if (col, row) in candidates
                                 else f'  {color_table[(col, row)][color]:-3d} ' for col in range(board_size))}|"""
                    for row in range(board_size)
                ]
            )
            tmp += '\n\n'
        return tmp

    @classmethod
    def filter_image(cls, _image: MatLike) -> tuple[Optional[MatLike], set]:
        # pylint: disable=too-many-locals,too-many-statements
        """implement filter for custom board"""

        def between(val: tuple[int, int, int], lower: list[int], upper: list[int]) -> bool:
            return all(lower[i] <= val[i] <= upper[i] for i in range(3))

        def is_tile(coord: tuple[int, int], hsv: tuple[int, int, int], rgb: tuple[int, int, int]) -> bool:
            r, g, b = rgb
            if abs(r - g) < 10 and abs(g - b) < 10 and abs(r - b) < 10:
                return True
            if coord in TRIPLE_WORDS:  # dark red
                return not (between(hsv, *cls.TWORD_COLOR0) or between(hsv, *cls.TWORD_COLOR1))
            if coord in DOUBLE_WORDS:  # light red
                return not (between(hsv, *cls.DWORD_COLOR0) or between(hsv, *cls.DWORD_COLOR1))
            if coord in TRIPLE_LETTER:  # dark blue
                return not between(hsv, *cls.TLETTER_COLOR)
            if coord in DOUBLE_LETTER:  # light blue
                return not between(hsv, *cls.DLETTER_COLOR)
            # green
            return not between(hsv, *cls.FIELD_COLOR)

        def distance(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> int:
            h1, s1, v1 = color1
            h2, s2, v2 = color2

            f = 255 // 2
            d1 = abs(((abs(h1 - h2) + f) % 255) - f)  # distance (H)SV
            d2 = abs(((abs(s1 - s2) + f) % 255) - f)  # distance H(S)V
            d3 = abs(((abs(v1 - v2) + f) % 255) - f)  # distance HS(V)

            erg = int((d1**2 + d2**2 + d3**2) ** 0.5)  # 3d distance
            return erg

        def find_tiles(coord: tuple[int, int], hsv_table: dict, rgb_table: dict, visited: set, candidates: set) -> None:
            col, row = coord
            if coord in visited:
                return
            visited.add(coord)
            candidates.add(coord)

            to_search = set()
            if col < 14:
                to_search.add((col + 1, row))
            if col > 0:
                to_search.add((col - 1, row))
            if row < 14:
                to_search.add((col, row + 1))
            if row > 0:
                to_search.add((col, row - 1))

            (h1, s1, v1) = hsv_table[coord]
            for coord2 in to_search:
                (h2, s2, v2) = hsv_table[coord2]
                (r, g, b) = rgb_table[coord2]
                if distance((h1, s1, v1), (h2, s2, v2)) < 30 or (abs(h1 - h2) < 75 and abs(s1 - s2) < 15 and abs(v1 - v2) < 25):
                    # small euclidic distance or minor diference in saturation / value
                    find_tiles(coord2, hsv_table, rgb_table, visited, candidates)
                elif abs(h1 - h2) < 15 and abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:
                    # h1 ~= h2 and R ~= G ~= B (=> gray)
                    find_tiles(coord2, hsv_table, rgb_table, visited, candidates)
                else:
                    logging.debug(
                        f"{chr(ord('A') + coord[1])}{coord[0]+1} - remove {chr(ord('A') + coord2[1])}{coord2[0]+1} "
                        f"dist={distance((h1, s1, v1), (h2, s2, v2))} {(r, g, b)=}"
                    )

        def autocontrast(image):
            from PIL import ImageOps

            pil_img: Image.Image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            pil_img = ImageOps.autocontrast(pil_img)
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        def adjust_gamma(image: MatLike, gamma: float = 1.0):
            # build a lookup table mapping the pixel values [0, 255] to
            # their adjusted gamma values
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype('uint8')
            # apply gamma correction using the lookup table
            return cv2.LUT(image, table)

        # check for gamma correction
        image = _image.copy()
        warped_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        (_, _, average_v) = cv2.mean(warped_hsv)[:3]
        if average_v < 65:
            logging.warning(f'>>> {average_v=} gamma correction 1.3')
            image = adjust_gamma(image=image, gamma=1.3)
            image = autocontrast(image=image)
        elif average_v < 90:
            logging.warning(f'>>>  {average_v=} gamma correction 1.1')
            image = adjust_gamma(image=image, gamma=1.1)
            image = autocontrast(image=image)

        result = np.zeros(image.shape, dtype='uint8')
        hsv_table: dict = {}
        rgb_table: dict = {}

        for col in range(15):
            for row in range(15):
                # 1600 pixel
                px_col = int(OFFSET + (row * GRID_H))
                px_row = int(OFFSET + (col * GRID_W))
                segment = image[px_col + 5 : px_col + GRID_H - 5, px_row + 5 : px_row + GRID_W - 5]
                info = image[px_col + 1 : px_col + GRID_H - 1, px_row + 1 : px_row + GRID_W - 1]

                pil_img = Image.fromarray(cv2.cvtColor(segment, cv2.COLOR_BGR2RGB))
                pil_img = pil_img.quantize(colors=3, method=Image.Quantize.FASTOCTREE)

                pil_rgb = pil_img.convert(mode='RGB')
                color_rgb = sorted(pil_rgb.getcolors(), reverse=True)[0][1]  # type: ignore # mypy bug 16788
                rgb_table[(col, row)] = color_rgb

                pil_hsv = pil_img.convert(mode='HSV')
                color_hsv_count, color_hsv = sorted(pil_hsv.getcolors(), reverse=True)[0]  # type: ignore # mypy bug 16788
                hsv_table[(col, row)] = color_hsv

                # swap rgb to bgr
                if is_tile((col, row), color_hsv, color_rgb):  # type: ignore
                    info[:, :, 2], info[:, :, 1], info[:, :, 0] = color_rgb  # type: ignore
                else:
                    info[:, :, 2], info[:, :, 1], info[:, :, 0] = (0, 0, 0)

                if config.development_recording and color_hsv != (0, 0, 0) and color_hsv[2] > 5:  # type: ignore
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    scale = 0.33
                    color = (255, 255, 255)
                    info = cv2.putText(info, f'{color_hsv[0]}', (1, 10), font, scale, color, 1, cv2.FILLED)  # type: ignore
                    info = cv2.putText(info, f'{color_hsv[1]}', (1, 20), font, scale, color, 1, cv2.FILLED)  # type: ignore
                    info = cv2.putText(info, f'{color_hsv[2]}', (1, 30), font, scale, color, 1, cv2.FILLED)  # type: ignore
                    info = cv2.putText(info, f'{color_hsv_count}', (1, 45), font, scale, color, 1, cv2.FILLED)
                result[px_col + 1 : px_col + GRID_H - 1, px_row + 1 : px_row + GRID_W - 1] = info

        candidates: set = set()
        find_tiles(coord=(7, 7), hsv_table=hsv_table, rgb_table=rgb_table, visited=set(), candidates=candidates)
        logging.debug(f'\n{cls.log_color_table(color_table=hsv_table, candidates=candidates)}')

        if any(x in candidates for x in [(6, 7), (7, 6), (8, 7), (7, 8)]):
            logging.debug(f'candidates:\n{cls.log_candidates(candidates=candidates)}')
            return result, candidates
        logging.debug('no word detected')
        return result, set()


# test and debug
def main():  # pylint: disable=too-many-locals
    """main function for test and debug"""

    import sys

    from numpy import hstack, vstack

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
    for fn in files:
        image = cv2.imread(fn)
        warped = Custom2012PILBoard.warp(image)

        result, tiles_candidates = Custom2012PILBoard.filter_image(_image=warped.copy())

        mask = np.zeros(warped.shape[:2], dtype='uint8')
        for col, row in tiles_candidates:
            px_col = int(OFFSET + (row * GRID_H))
            px_row = int(OFFSET + (col * GRID_W))
            mask[px_col : px_col + GRID_H, px_row : px_row + GRID_W] = 255

        masked = cv2.bitwise_and(warped, warped, mask=mask)
        blend = cv2.addWeighted(warped, 0.3, masked, 0.7, 0.0)
        result1 = hstack([warped, blend])
        result2 = hstack([result, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)])  # type: ignore
        result = vstack([result1, result2])

        cv2.imshow(f'{fn}', result)
        cv2.waitKey()
        cv2.destroyWindow(f'{fn}')


if __name__ == '__main__':
    main()
