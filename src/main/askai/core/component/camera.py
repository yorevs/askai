#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.components
      @file: recorder.py
   @created: Wed, 22 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import atexit
from pathlib import Path
from typing import TypeAlias, Optional

import cv2
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.zoned_datetime import now_ms
from retry import retry

from askai.__classpath__ import classpath
from askai.core.component.cache_service import PICTURE_DIR
from askai.core.support.utilities import display_text

InputDevice: TypeAlias = tuple[int, str]


class Camera(metaclass=Singleton):
    """Provide an interface to record voice using the microphone device."""

    INSTANCE: "Camera"

    RESOURCE_DIR: Path = classpath.resource_path()

    def __init__(self):
        self._cam = None
        self._anterior = 0
        self._cascPath = str(Path.joinpath(self.RESOURCE_DIR, "frontal_face_detection.xml"))
        self._faceCascade = cv2.CascadeClassifier(self._cascPath)
        self._initialize()

    @retry(tries=3, backoff=1)
    def capture(self, filename: str | None = None) -> Optional[str]:
        """Capture a WebCam frame (take a photo)."""

        if not self._cam.isOpened():
            display_text(f"%HOM%%ED2%Error: Camera is not open!%NC%")
            return None

        timestamp: int = now_ms()
        filepath = str(Path.joinpath(PICTURE_DIR, filename or f"ASKAI-{timestamp}.jpg"))
        display_text("Smile...")
        ret, photo = self._cam.read()

        if not ret:
            print('Failed to capture the camera!')
            return None

        self.detect_faces(photo, timestamp)
        cv2.imwrite(filepath, photo)

        return filepath

    def detect_faces(self, photo, timestamp) -> None:
        """Whether to detect all faces in the photo."""
        # Face detection
        gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
        faces = self._faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(photo, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if self._anterior != len(faces):
            self._anterior = len(faces)
            print("faces: " + str(len(faces)) + " at " + str(timestamp))

    @retry(tries=3, backoff=1)
    def _initialize(self) -> None:
        """Initialize the camera."""
        self._cam = cv2.VideoCapture(0)
        ret, _ = self._cam.read()
        if not ret:
            print('Failed to initialize the camera !')
        atexit.register(self._shutdown)

    def _shutdown(self) -> None:
        """Shutdown the camera."""
        if self._cam.isOpened():
            print("Shutting down camera!")
            self._cam.release()


assert (camera := Camera().INSTANCE) is not None

if __name__ == '__main__':
    while (done := input('Press [Enter] to take photo')) not in ['e', 'q']:
        camera.capture()
