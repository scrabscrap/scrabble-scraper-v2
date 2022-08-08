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

Mat = np.ndarray[int, np.dtype[np.generic]]

visualLogger = logging.getLogger("visualLogger")


class Custom:
    last_warp = None

    @staticmethod
    def warp(__image: Mat) -> Mat:

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
            # will have the minimum difference and the bottom-left will
            # have the maximum difference
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
            logging.debug(f"warp calculation {rect}")

            # evtl. auch nur eine Heuristik bzgl. der Abweichungen der Ecken?
            (x1, y1) = rect[0]
            (w1, y2) = rect[1]
            (w2, h1) = rect[2]
            (x2, h2) = rect[3]
            if abs(x1 - x2) > 40 or x1 < 15 or x2 < 15:
                if Custom.last_warp is not None:
                    rect[0][0] = Custom.last_warp[0][0]
                    rect[3][0] = Custom.last_warp[3][0]
                else:
                    x = max(x1, x2)
                    rect[0][0] = rect[3][0] = x
                    logging.warning(f"korrigiere x auf {x}")
            if abs(w1 - w2) > 40 or w1 > 1490 or w2 > 1490:
                if Custom.last_warp is not None:
                    rect[1][0] = Custom.last_warp[1][0]
                    rect[2][0] = Custom.last_warp[2][0]
                else:
                    w = min(w1, w2)
                    rect[1][0] = rect[2][0] = w
                    logging.warning(f"korrigiere w auf {w}")
            if abs(y1 - y2) > 40 or y1 < 15 or y2 < 15:
                if Custom.last_warp is not None:
                    rect[0][1] = Custom.last_warp[0][1]
                    rect[1][1] = Custom.last_warp[1][1]
                else:
                    y = max(y1, y2)
                    rect[0][1] = rect[1][1] = y
                    logging.warning(f"korrigiere y auf {y}")
            if abs(h1 - h2) > 40 or h1 > 1490 or h2 > 1490:
                if Custom.last_warp is not None:
                    rect[2][1] = Custom.last_warp[2][1]
                    rect[3][1] = Custom.last_warp[3][1]
                else:
                    h = min(h1, h2)
                    rect[2][1] = rect[3][1] = h
                    logging.warning(f"korrigiere h auf {h}")

            # if abs(x1 - x2) > 40 or abs(w1 - w2) > 40 or abs(y1 - y2) > 40 or abs(h1 - h2) > 40:
            #     # or x1 < 15 or y1 < 15 \
            #     #     or w1 > 1485 or y2 < 15 or w2 > 1485 or h1 > 1485 or x2 < 15 or h2 > 1485:
            #     if last_warp is not None:
            #         rect = last_warp
            #     else:
            #         logging.error("es kann keine sinnvolle Transformation ermittelt werden")
            #     logging.warning(f"korrigiere rest auf {rect}")
            # else:

        # construct our destination points which will be used to
        # map the screen to a top-down, "birds eye" view
        dst = np.array([
            [0, 0],
            [800, 0],
            [800, 800],
            [0, 800]], dtype="float32")

        # calculate the perspective transform matrix and warp
        # the perspective to grab the screen
        Custom.last_warp = rect
        m = cv2.getPerspectiveTransform(rect, dst)
        result = cv2.warpPerspective(__image, m, (800, 800))
        visualLogger.debug(VisualRecord("warp_custom", [result], fmt="png"))
        return result

    @staticmethod
    def filter_image(_image: Mat) -> tuple[Mat, set]:
        # Farbmodell LAB, 100px
        tmp_img = cv2.GaussianBlur(_image, (7, 7), 0)
        tmp_img = cv2.resize(tmp_img, (200, 200), interpolation=cv2.INTER_AREA)
        lab = cv2.cvtColor(tmp_img, cv2.COLOR_BGR2LAB)
        _, a, b = cv2.split(lab)
        image = cv2.merge((a, b))
        image = image.reshape((200 * 200, 2))
        image = np.float32(image)

        # Color Quantization
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 8, 2.0)
        k = 4
        _, labels_, _ = cv2.kmeans(image, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        clustering = np.reshape(np.array(labels_, dtype=np.uint8), (200, 200))
        # Sort the cluster labels in order of the frequency with which they occur.
        sorted_labels = sorted([n for n in range(k)], key=lambda _x: -np.sum(clustering == _x))
        # Initialize K-means grayscale image; set pixel colors based on clustering.
        kmeans_image = np.zeros((200, 200), dtype=np.uint8)
        for i, label in enumerate(sorted_labels):
            kmeans_image[clustering == label] = int(255 / (k - 1)) * i * 50

        # Farbe des Mittelsteines
        y = 94  # 47  # (3,125 + (7*6,25)
        x = 94  # 47  # (3,125 + (7*6,25)
        field = kmeans_image[y:y + 12, x:x + 12]
        a, cnts = np.unique(field, return_counts=True)
        high_freq_element = a[cnts.argmax()]
        kmeans_image[kmeans_image != high_freq_element] = 0

        # auf gesamte Fläche ausdehnen
        set_of_tiles = set()
        for row in range(0, 15):
            for col in range(0, 15):
                y = int(6.25 + (row * 12.5))
                x = int(6.25 + (col * 12.5))
                field = kmeans_image[y:y + 12, x:x + 12]
                a, cnts = np.unique(field, return_counts=True)
                if a[cnts.argmax()] != 0:
                    logging.debug(f"{chr(ord('A') + row)}{col + 1:2}: {cnts} ")
                    set_of_tiles.add((col, row))

        # kein Wort gelegt
        if (6, 7) not in set_of_tiles and \
                (7, 6) not in set_of_tiles and \
                (8, 7) not in set_of_tiles and \
                (7, 8) not in set_of_tiles:
            return kmeans_image, set()
        return kmeans_image, set_of_tiles
