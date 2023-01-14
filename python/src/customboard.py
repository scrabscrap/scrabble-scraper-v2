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

import cv2
import numpy as np
from vlogging import VisualRecord

from gameboard import GameBoard

Mat = np.ndarray[int, np.dtype[np.generic]]

visualLogger = logging.getLogger("visualLogger")

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


class CustomBoard(GameBoard):
    """ Implentation custom scrabble board analysis """
    last_warp = None

    @staticmethod
    def warp(__image: Mat) -> Mat:
        """" implement warp of a custom board """

        rect = CustomBoard.find_board(__image)

        # construct our destination points which will be used to
        # map the screen to a top-down, "birds eye" view
        dst = np.array([
            [0, 0],
            [800, 0],
            [800, 800],
            [0, 800]], dtype="float32")

        # calculate the perspective transform matrix and warp
        # the perspective to grab the screen
        CustomBoard.last_warp = rect
        matrix = cv2.getPerspectiveTransform(rect, dst)
        result = cv2.warpPerspective(__image, matrix, (800, 800))
        visualLogger.debug(VisualRecord("warp_custom", [result], fmt="png"))
        return result

    @staticmethod
    def filter_image(_image: Mat) -> tuple[Mat, set]:
        """ implement filter for custom board """

        # tmp_img = cv2.GaussianBlur(_image, (7, 7), 0)
        tmp_img = cv2.bilateralFilter(_image, 9, 75, 75)  # blur but preserve edges
        tmp_img = cv2.resize(tmp_img, (200, 200), interpolation=cv2.INTER_AREA)
        lab = cv2.cvtColor(tmp_img, cv2.COLOR_BGR2LAB)
        _, channel_a, channel_b = cv2.split(lab)
        image = cv2.merge((channel_a, channel_b))
        image = image.reshape((200 * 200, 2))
        image = np.float32(image)
        visualLogger.debug(VisualRecord("lab", [lab], fmt="png"))

        # Color Quantization
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 8, 1.0)
        k = 4
        _, labels_, _ = cv2.kmeans(image, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
        clustering = np.reshape(np.array(labels_, dtype=np.uint8), (200, 200))
        logging.debug(f"clustering {clustering} ")
        # Sort the cluster labels in order of the frequency with which they occur.
        sorted_labels = sorted([n for n in range(k)], key=lambda _x: -np.sum(clustering == _x))
        logging.debug(f"sorted labels {sorted_labels} ")

        # Initialize K-means grayscale image; set pixel colors based on clustering.
        kmeans_image = np.zeros((200, 200), dtype=np.uint8)
        for i, label in enumerate(sorted_labels):
            kmeans_image[clustering == label] = int(255 / (k - 1)) * i * 50

        # Farbe des Mittelsteines
        y = 94  # 47  # (3,125 + (7*6,25)
        x = 94  # 47  # (3,125 + (7*6,25)
        field = kmeans_image[y:y + 12, x:x + 12]
        channel_a, cnts = np.unique(field, return_counts=True)
        high_freq_element = channel_a[cnts.argmax()]
        kmeans_image[kmeans_image != high_freq_element] = 0
        logging.debug(f">> middle: {cnts} -- {channel_a} ")

        # auf gesamte Fläche ausdehnen
        set_of_tiles = set()
        for row in range(0, 15):
            for col in range(0, 15):
                y = int(6.25 + (row * 12.5))
                x = int(6.25 + (col * 12.5))
                field = kmeans_image[y:y + 12, x:x + 12]
                channel_a, cnts = np.unique(field, return_counts=True)
                logging.debug(f">> {chr(ord('A') + row)}{col + 1:2}: {cnts} -- {channel_a} ")
                if channel_a[cnts.argmax()] != 0:
                    logging.debug(f"{chr(ord('A') + row)}{col + 1:2}: {cnts} ")
                    set_of_tiles.add((col, row))

        # kein Wort gelegt
        visualLogger.debug(VisualRecord("kmeans", [kmeans_image], fmt="png"))

        if (6, 7) not in set_of_tiles and \
                (7, 6) not in set_of_tiles and \
                (8, 7) not in set_of_tiles and \
                (7, 8) not in set_of_tiles:
            return kmeans_image, set()
        logging.debug(f'candidates {set_of_tiles}')
        return kmeans_image, set_of_tiles
