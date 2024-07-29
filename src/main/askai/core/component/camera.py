#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.components
      @file: recorder.py
   @created: Wed, 22 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import atexit
import logging as log
from collections import namedtuple
from os.path import basename
from typing import Optional, TypeAlias

import cv2
import numpy
import pause
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import hash_text
from retry import retry

from askai.core.component.cache_service import PHOTO_DIR
from askai.core.support.utilities import display_text, build_img_path

InputDevice: TypeAlias = tuple[int, str]

ImageData: TypeAlias = numpy.ndarray

ImageFile = namedtuple('ImageFile', ['img_id', 'img_path', 'img_category', 'img_name'])


class Camera(metaclass=Singleton):
    """Provide an interface to capture WebCam photos."""

    INSTANCE: "Camera"

    PHOTO_CATEGORY: str = 'photos'

    @staticmethod
    def _countdown(count: int) -> None:
        """Display a countdown before taking a photo."""
        i = count
        print()
        display_text(f"Smile {str(i) + ' '}")
        while i:
            display_text(f"Smile {str(i) + ' '}", erase_last=True)
            pause.seconds(1)
            i -= 1

    def __init__(self):
        self._cam = None

    def capture(self, filename: str | None = None, countdown: int = 0) -> Optional[tuple[ImageFile, ImageData]]:
        """Capture a WebCam frame (take a photo)."""

        self._initialize()

        if not self._cam.isOpened():
            display_text(f"%HOM%%ED2%Error: Camera is not open!%NC%")
            return None

        if countdown > 0:
            self._countdown(countdown)

        ret, photo = self._cam.read()

        if not ret:
            log.error("Failed to take a photo from WebCam!")
            return None

        final_path: str = build_img_path(PHOTO_DIR, filename, '-photo.jpg')
        cv2.imwrite(final_path, photo)
        photo_file = ImageFile(hash_text(basename(final_path)), final_path, self.PHOTO_CATEGORY, 'Photo')
        log.info("WebCam photo taken: '%s'", photo_file)

        return photo_file, photo

    @retry(tries=3, backoff=1)
    def _initialize(self) -> None:
        """Initialize the camera component."""
        # Init the WebCam.
        if not self._cam or not self._cam.isOpened():
            self._cam = cv2.VideoCapture(0)
            ret, img = self._cam.read()
            log.info("Starting the WebCam device")
            if not (ret and img is not None):
                log.error("Failed to initialize the WebCam device !")
                return
            atexit.register(self._shutdown)

    @retry(tries=3, backoff=1)
    def _shutdown(self) -> None:
        """Shutdown the camera."""
        if self._cam and self._cam.isOpened():
            log.info("Shutting down the WebCam device")
            self._cam.release()


assert (camera := Camera().INSTANCE) is not None
