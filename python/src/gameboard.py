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

from typing import Optional

import cv2
import imutils
import numpy as np
from cv2.typing import MatLike

from config import config
from util import TWarp


class GameBoard:
    """Implementation of a scrabble board analysis"""

    @classmethod
    def warp(cls, image) -> MatLike:  # type: ignore
        """ " implement warp of a game board"""
        pass

    @classmethod
    def filter_image(cls, _img: MatLike) -> tuple[Optional[MatLike], set]:
        """implement filter for game board"""
        return _img, set()

    @staticmethod
    def find_board(image) -> TWarp:
        """try to find the game board border"""
        if config.video_warp_coordinates is not None:
            rect = np.array(config.video_warp_coordinates, dtype='float32')
        else:
            # based on: https://www.pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/
            (blue, _, _) = cv2.split(image.copy())

            # Otsu's thresholding after Gaussian filtering
            blur = cv2.GaussianBlur(blue, (5, 5), 0)
            _, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
            dilated = cv2.dilate(th3, kernel)

            cnts = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)  # type: ignore
            pts = None
            for contour in cnts:
                peri = cv2.arcLength(contour, True)  # type: ignore[arg-type]
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)  # type: ignore[arg-type]
                if len(approx) == 4:
                    pts = approx.reshape(4, 2)
                    break
            rect = np.zeros((4, 2), dtype='float32')
            if pts is None:
                rect[0] = [0, 0]
                rect[1] = [image.shape[1] - 1, 0]
                rect[2] = [image.shape[1] - 1, image.shape[0] - 1]
                rect[3] = [0, image.shape[0] - 1]
                return rect
            # the top-left point has the smallest sum whereas the
            # bottom-right has the largest sum
            sums = pts.sum(axis=1)
            rect[0] = pts[np.argmin(sums)]
            rect[2] = pts[np.argmax(sums)]

            # compute the difference between the points -- the top-right
            # will have the minumum difference and the bottom-left will
            # have the maximum difference
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
        return rect
