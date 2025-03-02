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
from typing import Optional, Set, Tuple

import cv2
import numpy as np
from cv2.typing import MatLike

from customboard import CustomBoard
from game_board.board import DOUBLE_LETTER, DOUBLE_WORDS, GRID_H, GRID_W, OFFSET, TRIPLE_LETTER, TRIPLE_WORDS


def _create_masks() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    def create_mask(shape=(800, 800)) -> np.ndarray:
        return np.zeros(shape, dtype='uint8')

    def apply_mask(
        mask: np.ndarray, coordinates: Set[Tuple[int, int]], grid_h: int, grid_w: int, offset: int, field: np.ndarray
    ):
        for col, row in coordinates:
            px_col, px_row = int(offset + row * grid_h), int(offset + col * grid_w)
            mask[px_col : px_col + grid_h, px_row : px_row + grid_w] = 255
            field[px_col : px_col + grid_h, px_row : px_row + grid_w] = 0

    field = np.full((800, 800), 255, dtype='uint8')
    masks = {'tword': create_mask(), 'dword': create_mask(), 'tletter': create_mask(), 'dletter': create_mask()}

    for key, coords in zip(masks.keys(), [TRIPLE_WORDS, DOUBLE_WORDS, TRIPLE_LETTER, DOUBLE_LETTER]):
        apply_mask(masks[key], coords, GRID_H, GRID_W, OFFSET, field)

    return masks['tword'], masks['dword'], masks['tletter'], masks['dletter'], field


board_tword, board_dword, board_tletter, board_dletter, board_field = _create_masks()


class Custom2020Board(CustomBoard):
    """Implementation custom 2020 scrabble board analysis"""

    # layout 2020 dark
    TLETTER = [[160, 200, 100], [180, 255, 255]]
    DLETTER = [[50, 40, 0], [140, 255, 180]]
    TWORD = [[10, 120, 90], [50, 255, 200]]
    DWORD = [[0, 200, 100], [40, 255, 255]]
    FIELD = [[70, 0, 0], [110, 220, 200]]

    # TILES_THRESHOLD = 1000 # use configured threshold

    @classmethod
    def filter_image(cls, color: MatLike) -> tuple[Optional[MatLike], set]:
        def create_mask(hsv: MatLike, color_range, board_mask) -> np.ndarray:
            tmp = cv2.bitwise_and(hsv, hsv, mask=board_mask)
            mask = np.zeros((800, 800), dtype='uint8')
            for i in range(0, len(color_range), 2):
                mask |= cv2.inRange(tmp, np.array(color_range[i]), np.array(color_range[i + 1]))
            return mask

        def filter_color(color: MatLike) -> MatLike:
            hsv = cv2.cvtColor(color, cv2.COLOR_BGR2HSV)

            mask_tword = create_mask(hsv, cls.TWORD, board_tword)
            mask_dword = create_mask(hsv, cls.DWORD, board_dword)
            mask_tletter = create_mask(hsv, cls.TLETTER, board_tletter)
            mask_dletter = create_mask(hsv, cls.DLETTER, board_dletter)
            mask_field = create_mask(hsv, cls.FIELD, board_field)
            mask_result = mask_tword | mask_dword | mask_field | mask_tletter | mask_dletter
            # invert mask
            mask_result = cv2.bitwise_not(mask_result)  # type: ignore
            return cv2.bitwise_and(color, color, mask=mask_result)

        gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Thresholding for gray image
        segment = gray_blur[
            int(OFFSET + (7 * GRID_H)) : int(OFFSET + (7 * GRID_H)) + GRID_H,
            int(OFFSET + (7 * GRID_W)) : int(OFFSET + (7 * GRID_W)) + GRID_W,
        ]
        T, _ = cv2.threshold(segment, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        segment = gray_blur[int(OFFSET) : int(OFFSET) + (GRID_H * 14), int(OFFSET) : int(OFFSET) + (GRID_W * 14)]
        T1, _ = cv2.threshold(gray_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        _, thresh = cv2.threshold(gray_blur, int((T + T1) / 2), 255, cv2.THRESH_BINARY)

        print(f'{T=} {T1=} use={int((T + T1) / 2)}')

        color_thresh = cv2.bitwise_and(color, color, mask=thresh)
        filtered = filter_color(color_thresh)
        gray_filtered = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)

        candidates, filtered_pixels = set(), {}
        for col in range(15):
            for row in range(15):
                px_col = int(OFFSET + (row * GRID_H))
                px_row = int(OFFSET + (col * GRID_W))
                segment = gray_filtered[px_col + 2 : px_col + GRID_H - 2, px_row + 2 : px_row + GRID_W - 2]
                number_of_not_black_pix: int = np.sum(segment != 0)
                filtered_pixels[(col, row)] = number_of_not_black_pix
                if number_of_not_black_pix > cls.TILES_THRESHOLD:
                    candidates.add((col, row))
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            result = cv2.hconcat((color, cv2.cvtColor(gray_filtered, cv2.COLOR_GRAY2BGR)))  # pylint: disable=C0301
            logging.debug(f'filtered pixels:\n{cls.log_pixels(filtered_pixels=filtered_pixels)}')
            logging.debug(f'candidates:\n{cls.log_candidates(candidates=candidates)}')
        else:
            result = None
        return result, candidates
