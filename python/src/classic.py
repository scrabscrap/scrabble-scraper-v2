"""
 This file is part of the scrabble-scraper distribution (https://github.com/scrabscrap/scrabble-scraper)
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
import imutils
import numpy as np
from vlogging import VisualRecord

from config import config
from game_board.board import GRID_H, GRID_W, get_x_position, get_y_position

Mat = np.ndarray[int, np.dtype[np.generic]]

visualLogger = logging.getLogger("visualLogger")
last_warp = None


class Classic:

    @staticmethod
    def warp(__image):

        if config.WARP_COORDINATES is not None:
            rect = np.array(config.WARP_COORDINATES, dtype="float32")
        else:
            # based on: https://www.pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/
            (blue, _, _) = cv2.split(__image.copy())

            # Otsu's thresholding after Gaussian filtering
            blur = cv2.GaussianBlur(blue, (5, 5), 0)
            ret3, th3 = cv2.threshold(
                blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
            dilated = cv2.dilate(th3, kernel)

            cnts = cv2.findContours(
                dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:1]
            c = cnts[0]
            peri = 1
            approx = cv2.approxPolyDP(c, peri, True)
            while len(approx) > 4:
                peri += 1
                approx = cv2.approxPolyDP(c, peri, True)

            pts = approx.reshape(4, 2)
            rect = np.zeros((4, 2), dtype="float32")

            # the top-left point has the smallest sum whereas the
            # bottom-right has the largest sum
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]

            # compute the difference between the points -- the top-right
            # will have the minumum difference and the bottom-left will
            # have the maximum difference
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]

        # now that we have our rectangle of points, let's compute
        # the width of our new image
        (tl, tr, br, bl) = rect
        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))

        # ...and now for the height of our new image
        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))

        # take the maximum of the width and height values to reach
        # our final dimensions
        max_width = max(int(width_a), int(width_b))
        max_height = max(int(height_a), int(height_b))

        # construct our destination points which will be used to
        # map the screen to a top-down, "birds eye" view
        dst = np.array([
            [0, 0],
            [max_width, 0],
            [max_width, max_height],
            [0, max_height]], dtype="float32")

        # calculate the perspective transform matrix and warp
        # the perspective to grab the screen
        m = cv2.getPerspectiveTransform(rect, dst)
        result = cv2.warpPerspective(__image, m, (max_width, max_height))
        # crop bild auf 10mm Rand
        # größe = 360mm x 360mm
        # abschneiden: oben: 7mm links: 15mm rechts 15mm unten 23mm
        # ergibt: 330mm x 330mm
        # img[y:y + h, x:x + w]
        ct = int((max_height / 360) * 7)
        cw = int((max_width / 360) * 15)
        cb = int((max_height / 360) * 23)
        crop = result[ct:max_height - cb, cw:max_width - cw]
        resized = cv2.resize(crop, (800, 800))
        visualLogger.debug(VisualRecord("warp_classic", [resized, result, crop], fmt="png"))
        return resized

    @staticmethod
    def filter_image(_img) -> tuple[Mat, set]:
        _gray = cv2.cvtColor(_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        blank_grid = 255 - thresh.astype('uint8')
        blank_grid = cv2.erode(blank_grid, None, iterations=4)
        blank_grid = cv2.dilate(blank_grid, None, iterations=2)
        blank_grid = cv2.erode(blank_grid, None, iterations=4)
        blank_grid = cv2.dilate(blank_grid, None, iterations=2)

        mark_grid = cv2.GaussianBlur(thresh, (5, 5), 0)
        mark_grid = cv2.erode(mark_grid, None, iterations=4)
        mark_grid = cv2.dilate(mark_grid, None, iterations=4)
        _, mark_grid = cv2.threshold(mark_grid, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        _tiles_candidates = set()
        _blank_candidates = {}
        Classic._mark_grid((7, 7), mark_grid, blank_grid, _tiles_candidates, _blank_candidates)  # starte in der Mitte

        return _gray, _tiles_candidates

    @staticmethod
    def _mark_grid(coord: tuple[int, int], _grid, _blank_grid, _board: set, _blank_candidates: dict):
        (col, row) = coord
        if col not in range(0, 15):
            return
        if row not in range(0, 15):
            return
        if coord in _board:
            return
        _y = get_y_position(row)
        _x = get_x_position(col)
        # schneide Gitterelement aus
        _image = _grid[_y + 12:_y + GRID_H - 12, _x + 12:_x + GRID_W - 12]
        percentage = np.count_nonzero(_image) * 100 // _image.size
        if percentage > 60:
            _board.add(coord)
            _img_blank = _blank_grid[_y + 15:_y + GRID_H - 15, _x + 15:_x + GRID_W - 15]
            percentage = np.count_nonzero(_img_blank) * 100 // _img_blank.size
            if percentage > 85:
                _blank_candidates[coord] = ('_', 76 + (percentage - 90) * 2)
            Classic._mark_grid((col + 1, row), _grid, _blank_grid, _board, _blank_candidates)
            Classic._mark_grid((col - 1, row), _grid, _blank_grid, _board, _blank_candidates)
            Classic._mark_grid((col, row + 1), _grid, _blank_grid, _board, _blank_candidates)
            Classic._mark_grid((col, row - 1), _grid, _blank_grid, _board, _blank_candidates)
