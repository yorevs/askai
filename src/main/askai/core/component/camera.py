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
from os.path import basename
from pathlib import Path
from typing import Optional, TypeAlias

import cv2
import pause
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import hash_text
from retry import retry

from askai.__classpath__ import classpath
from askai.core.component.cache_service import PHOTO_DIR, FACE_DIR
from askai.core.component.recognizer import ImageFile, ImageData, recognizer, ImageMetadata
from askai.core.support.utilities import display_text, build_img_path

InputDevice: TypeAlias = tuple[int, str]


class Camera(metaclass=Singleton):
    """Provide an interface to capture WebCam photos."""

    INSTANCE: "Camera"

    RESOURCE_DIR: Path = classpath.resource_path()

    ALG: str = "haarcascade_frontalface_default.xml"

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
        self._cascPath: Path = Path.joinpath(self.RESOURCE_DIR, self.ALG)
        self._haarFaceCascade = cv2.CascadeClassifier(str(self._cascPath))

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
        photo_file = ImageFile(hash_text(basename(final_path)), final_path, recognizer.PHOTO_CATEGORY, 'Photo')
        recognizer.store_image(photo_file)
        log.info("WebCam photo captured: '%s'", photo_file)

        return photo_file, photo

    def detect_faces(self, photo: ImageData, filename: str) -> tuple[list[ImageFile], list[ImageData]]:
        """Detect all faces in the photo."""

        # Face detection
        gray_img = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
        faces = self._haarFaceCascade.detectMultiScale(
            gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
        )
        log.info("Detected faces: %d", len(faces))
        face_files: list[ImageFile] = list()
        face_datas: list[ImageData] = list()

        if len(faces) > 0:
            # For each face detected on the photo.
            for x, y, w, h in faces:
                # Draw a rectangle around the detected faces.
                cv2.rectangle(photo, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cropped_face: ImageData = photo[y: y + h, x: x + w]
                final_path: str = build_img_path(FACE_DIR, filename, f'-face-{len(face_files)}.jpg')
                if cv2.imwrite(final_path, cropped_face):
                    face_file = ImageFile(hash_text(basename(final_path)), final_path, recognizer.FACE_CATEGORY, 'Face')
                    face_files.append(face_file)
                    face_datas.append(cropped_face)
                    log.info("Face file successfully saved: '%s' !", final_path)
                else:
                    log.error("Failed to save face file: '%s' !", final_path)
            recognizer.store_image(*face_files)

        return face_files, face_datas

    def identify(self) -> Optional[ImageMetadata]:
        """Identify the person in front of the WebCam."""
        _, photo = self.capture("ASKAI-ID-PHOTO", False)
        _ = self.detect_faces(photo, "ASKAI-ID-FACE")
        result = recognizer.search_face(photo)
        return next(iter(result), None)

    @retry(tries=3, backoff=1)
    def _initialize(self) -> None:
        """Initialize the camera device."""
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
        """Shutdown the camera device."""
        if self._cam and self._cam.isOpened():
            log.info("Shutting down the WebCam device")
            self._cam.release()


assert (camera := Camera().INSTANCE) is not None
