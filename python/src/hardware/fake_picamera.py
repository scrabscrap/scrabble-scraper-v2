"""
 This file is part of the scrabble-scraper-v2 distribution
 (https://github.com/scrabscrap/scrabble-scraper-v2)
 Copyright (c) 2023 Rainer Rohloff.

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
import numpy as np


class BGR:  # pylint: disable=too-few-public-methods
    """Fake class"""

    def __init__(self, sz):
        # constructor
        self.array = np.random.rand(*sz)

    def truncate(self, num):
        # pylint: disable=unused-argument
        """Fake method"""
        # refreshes the fake image
        self.array = np.random.rand(*self.array.shape)


# class picamera(object):
#     """Fake class"""
class PiCamera:
    """Fake class"""
    resolution = (0, 0)

    def __init__(self, resolution=None, framerate=None, sensor_mode=None):
        # empty constructor
        logging.warning(f'using fake raspberry pi camera resolution={resolution} / framerate {framerate} /  mode {sensor_mode}')
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # pylint: disable=unused-argument
        pass

    def close(self):
        """
        Fake: Finalizes the state of the camera.

        After successfully constructing a :class:`PiCamera` object, you should
        ensure you call the :meth:`close` method once you are finished with the
        camera (e.g. in the ``finally`` section of a ``try..finally`` block).
        This method stops all recording and preview activities and releases all
        resources associated with the camera; this is necessary to prevent GPU
        memory leaks.
        """
        pass

    def capture(self, output, format=None, use_video_port=False, resize=None, splitter_port=0, **options):
        # pylint: disable=unused-argument too-many-arguments redefined-builtin
        """
        Fake: Capture an image from the camera, storing it in *output*.

        If *output* is a string, it will be treated as a filename for a new
        file which the image will be written to. If *output* is not a string,
        but is an object with a ``write`` method, it is assumed to be a
        file-like object and the image data is appended to it (the
        implementation only assumes the object has a ``write`` method - no
        other methods are required but ``flush`` will be called at the end of
        capture if it is present). If *output* is not a string, and has no
        ``write`` method it is assumed to be a writeable object implementing
        the buffer protocol. In this case, the image data will be written
        directly to the underlying buffer (which must be large enough to accept
        the image data).

        If *format* is ``None`` (the default), the method will attempt to guess
        the required image format from the extension of *output* (if it's a
        string), or from the *name* attribute of *output* (if it has one). In
        the case that the format cannot be determined, a
        :exc:`PiCameraValueError` will be raised.

        If *format* is not ``None``, it must be a string specifying the format
        that you want the image output in. The format can be a MIME-type or
        one of the following strings:

        * ``'jpeg'`` - Write a JPEG file
        * ``'png'`` - Write a PNG file
        * ``'gif'`` - Write a GIF file
        * ``'bmp'`` - Write a Windows bitmap file
        * ``'yuv'`` - Write the raw image data to a file in YUV420 format
        * ``'rgb'`` - Write the raw image data to a file in 24-bit RGB format
        * ``'rgba'`` - Write the raw image data to a file in 32-bit RGBA format
        * ``'bgr'`` - Write the raw image data to a file in 24-bit BGR format
        * ``'bgra'`` - Write the raw image data to a file in 32-bit BGRA format
        * ``'raw'`` - Deprecated option for raw captures; the format is taken
          from the deprecated :attr:`raw_format` attribute

        The *use_video_port* parameter controls whether the camera's image or
        video port is used to capture images. It defaults to ``False`` which
        means that the camera's image port is used. This port is slow but
        produces better quality pictures. If you need rapid capture up to the
        rate of video frames, set this to ``True``.

        When *use_video_port* is ``True``, the *splitter_port* parameter
        specifies the port of the video splitter that the image encoder will be
        attached to. This defaults to ``0`` and most users will have no need to
        specify anything different. This parameter is ignored when
        *use_video_port* is ``False``. See :ref:`mmal` for more information
        about the video splitter.

        If *resize* is not ``None`` (the default), it must be a two-element
        tuple specifying the width and height that the image should be resized
        to.

        .. warning::

            If *resize* is specified, or *use_video_port* is ``True``, Exif
            metadata will **not** be included in JPEG output. This is due to an
            underlying firmware limitation.

        Certain file formats accept additional options which can be specified
        as keyword arguments. Currently, only the ``'jpeg'`` encoder accepts
        additional options, which are:

        * *quality* - Defines the quality of the JPEG encoder as an integer
          ranging from 1 to 100. Defaults to 85. Please note that JPEG quality
          is not a percentage and `definitions of quality`_ vary widely.

        * *restart* - Defines the restart interval for the JPEG encoder as a
          number of JPEG MCUs. The actual restart interval used will be a
          multiple of the number of MCUs per row in the resulting image.

        * *thumbnail* - Defines the size and quality of the thumbnail to embed
          in the Exif metadata. Specifying ``None`` disables thumbnail
          generation.  Otherwise, specify a tuple of ``(width, height,
          quality)``. Defaults to ``(64, 48, 35)``.

        * *bayer* - If ``True``, the raw bayer data from the camera's sensor
          is included in the Exif metadata.

        .. note::

            The so-called "raw" formats listed above (``'yuv'``, ``'rgb'``,
            etc.) do not represent the raw bayer data from the camera's sensor.
            Rather they provide access to the image data after GPU processing,
            but before format encoding (JPEG, PNG, etc). Currently, the only
            method of accessing the raw bayer data is via the *bayer* parameter
            described above.

        .. versionchanged:: 1.0
            The *resize* parameter was added, and raw capture formats can now
            be specified directly

        .. versionchanged:: 1.3
            The *splitter_port* parameter was added, and *bayer* was added as
            an option for the ``'jpeg'`` format

        .. versionchanged:: 1.11
            Support for buffer outputs was added.

        .. _definitions of quality: http://photo.net/learn/jpeg/#qual
        """
        pass

    def capture_continuous(self, output, format=None, use_video_port=False, resize=None,
                           splitter_port=0, burst=False, bayer=False, **options):
        # pylint: disable=unused-argument too-many-arguments redefined-builtin
        """
        Fake: Capture images continuously from the camera as an infinite iterator.

        This method returns an infinite iterator of images captured
        continuously from the camera. If *output* is a string, each captured
        image is stored in a file named after *output* after substitution of
        two values with the :meth:`~str.format` method. Those two values are:

        * ``{counter}`` - a simple incrementor that starts at 1 and increases
          by 1 for each image taken

        * ``{timestamp}`` - a :class:`~datetime.datetime` instance

        The table below contains several example values of *output* and the
        sequence of filenames those values could produce:

        .. tabularcolumns:: |p{80mm}|p{40mm}|p{10mm}|

        +--------------------------------------------+--------------------------------------------+-------+
        | *output* Value                             | Filenames                                  | Notes |
        +============================================+============================================+=======+
        | ``'image{counter}.jpg'``                   | image1.jpg, image2.jpg, image3.jpg, ...    |       |
        +--------------------------------------------+--------------------------------------------+-------+
        | ``'image{counter:02d}.jpg'``               | image01.jpg, image02.jpg, image03.jpg, ... |       |
        +--------------------------------------------+--------------------------------------------+-------+
        | ``'image{timestamp}.jpg'``                 | image2013-10-05 12:07:12.346743.jpg,       | (1)   |
        |                                            | image2013-10-05 12:07:32.498539, ...       |       |
        +--------------------------------------------+--------------------------------------------+-------+
        | ``'image{timestamp:%H-%M-%S-%f}.jpg'``     | image12-10-02-561527.jpg,                  |       |
        |                                            | image12-10-14-905398.jpg                   |       |
        +--------------------------------------------+--------------------------------------------+-------+
        | ``'{timestamp:%H%M%S}-{counter:03d}.jpg'`` | 121002-001.jpg, 121013-002.jpg,            | (2)   |
        |                                            | 121014-003.jpg, ...                        |       |
        +--------------------------------------------+--------------------------------------------+-------+

        1. Note that because timestamp's default output includes colons (:),
           the resulting filenames are not suitable for use on Windows. For
           this reason (and the fact the default contains spaces) it is
           strongly recommended you always specify a format when using
           ``{timestamp}``.

        2. You can use both ``{timestamp}`` and ``{counter}`` in a single
           format string (multiple times too!) although this tends to be
           redundant.

        If *output* is not a string, but has a ``write`` method, it is assumed
        to be a file-like object and each image is simply written to this
        object sequentially. In this case you will likely either want to write
        something to the object between the images to distinguish them, or
        clear the object between iterations. If *output* is not a string, and
        has no ``write`` method, it is assumed to be a writeable object
        supporting the buffer protocol; each image is simply written to the
        buffer sequentially.

        The *format*, *use_video_port*, *splitter_port*, *resize*, and
        *options* parameters are the same as in :meth:`capture`.

        If *use_video_port* is ``False`` (the default), the *burst* parameter
        can be used to make still port captures faster.  Specifically, this
        prevents the preview from switching resolutions between captures which
        significantly speeds up consecutive captures from the still port. The
        downside is that this mode is currently has several bugs; the major
        issue is that if captures are performed too quickly some frames will
        come back severely underexposed. It is recommended that users avoid the
        *burst* parameter unless they absolutely require it and are prepared to
        work around such issues.

        For example, to capture 60 images with a one second delay between them,
        writing the output to a series of JPEG files named image01.jpg,
        image02.jpg, etc. one could do the following::

            import time
            import picamera
            with picamera.PiCamera() as camera:
                camera.start_preview()
                try:
                    for i, filename in enumerate(
                            camera.capture_continuous('image{counter:02d}.jpg')):
                        print(filename)
                        time.sleep(1)
                        if i == 59:
                            break
                finally:
                    camera.stop_preview()

        Alternatively, to capture JPEG frames as fast as possible into an
        in-memory stream, performing some processing on each stream until
        some condition is satisfied::

            import io
            import time
            import picamera
            with picamera.PiCamera() as camera:
                stream = io.BytesIO()
                for foo in camera.capture_continuous(stream, format='jpeg'):
                    # Truncate the stream to the current position (in case
                    # prior iterations output a longer image)
                    stream.truncate()
                    stream.seek(0)
                    if process(stream):
                        break

        .. versionchanged:: 1.0
            The *resize* parameter was added, and raw capture formats can now
            be specified directly

        .. versionchanged:: 1.3
            The *splitter_port* parameter was added

        .. versionchanged:: 1.11
            Support for buffer outputs was added.
        """
        pass


class PiRGBArray:
    # pylint: disable=invalid-name too-few-public-methods
    """
    Fake: Produces a 3-dimensional RGB array from an RGB capture.

    This custom output class can be used to easily obtain a 3-dimensional numpy
    array, organized (rows, columns, colors), from an unencoded RGB capture.
    The array is accessed via the :attr:`~PiArrayOutput.array` attribute. For
    example::

        import picamera
        import picamera.array

        with picamera.PiCamera() as camera:
            with picamera.array.PiRGBArray(camera) as output:
                camera.capture(output, 'rgb')
                print('Captured %dx%d image' % (
                        output.array.shape[1], output.array.shape[0]))

    You can re-use the output to produce multiple arrays by emptying it with
    ``truncate(0)`` between captures::

        import picamera
        import picamera.array

        with picamera.PiCamera() as camera:
            with picamera.array.PiRGBArray(camera) as output:
                camera.resolution = (1280, 720)
                camera.capture(output, 'rgb')
                print('Captured %dx%d image' % (
                        output.array.shape[1], output.array.shape[0]))
                output.truncate(0)
                camera.resolution = (640, 480)
                camera.capture(output, 'rgb')
                print('Captured %dx%d image' % (
                        output.array.shape[1], output.array.shape[0]))

    If you are using the GPU resizer when capturing (with the *resize*
    parameter of the various :meth:`~PiCamera.capture` methods), specify the
    resized resolution as the optional *size* parameter when constructing the
    array output::

        import picamera
        import picamera.array

        with picamera.PiCamera() as camera:
            camera.resolution = (1280, 720)
            with picamera.array.PiRGBArray(camera, size=(640, 360)) as output:
                camera.capture(output, 'rgb', resize=(640, 360))
                print('Captured %dx%d image' % (
                        output.array.shape[1], output.array.shape[0]))
    """

    def __init__(self, cam, size):
        # pylint: disable=unused-argument invalid-name too-few-public-methods
        """Fake method"""
        self.array = BGR(size)

    def close(self) -> None:
        """Fake method"""
        pass
