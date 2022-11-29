
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
import cv2
import imutils
import numpy as np

from config import config

Mat = np.ndarray[int, np.dtype[np.generic]]


class GameBoard:
    """ Implementation of a scrabble board analysis """

    @staticmethod
    def warp(__image):
        """" implement warp of a game board """
        pass

    @staticmethod
    def filter_image(_img) -> tuple[Mat, set]:
        """ implement filter for game board """
        return _img

    @staticmethod
    def find_board(__image):
        """ try to find the game board border"""
        if config.video_warp_coordinates is not None:
            rect = np.array(config.video_warp_coordinates, dtype="float32")
        else:
            # based on: https://www.pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/
            (blue, _, _) = cv2.split(__image.copy())

            # Otsu's thresholding after Gaussian filtering
            blur = cv2.GaussianBlur(blue, (5, 5), 0)
            _, th3 = cv2.threshold(
                blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
            dilated = cv2.dilate(th3, kernel)

            cnts = cv2.findContours(
                dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:1]
            contour = cnts[0]
            peri = 1
            approx = cv2.approxPolyDP(contour, peri, True)
            while len(approx) > 4:
                peri += 1
                approx = cv2.approxPolyDP(contour, peri, True)

            pts = approx.reshape(4, 2)
            rect = np.zeros((4, 2), dtype="float32")

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
