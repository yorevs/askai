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

import chromadb
import cv2
import numpy
from PIL import Image
from chromadb.utils.data_loaders import ImageLoader
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import ensure_endswith
from hspylib.core.zoned_datetime import now_ms
from imgbeddings import imgbeddings
from retry import retry

from askai.__classpath__ import classpath
from askai.core.component.cache_service import PICTURE_DIR
from askai.core.support.langchain_support import lc_llm
from askai.core.support.utilities import display_text

InputDevice: TypeAlias = tuple[int, str]


class Camera(metaclass=Singleton):
    """Provide an interface to record voice using the microphone device."""

    INSTANCE: "Camera"

    RESOURCE_DIR: Path = classpath.resource_path()

    ALG: str = "haarcascade_frontalface_default.xml"

    def __init__(self):
        self._cam = None
        self._cascPath = str(Path.joinpath(self.RESOURCE_DIR, self.ALG))
        self._haarFaceCascade = cv2.CascadeClassifier(self._cascPath)
        self._initialize()

    @retry(tries=3, backoff=1)
    def capture(self, filename: str | None = None) -> Optional[str]:
        """Capture a WebCam frame (take a photo)."""

        if not self._cam.isOpened():
            display_text(f"%HOM%%ED2%Error: Camera is not open!%NC%")
            return None

        timestamp: int = now_ms()
        filepath: str = str(Path.joinpath(PICTURE_DIR, basename(filename or f"ASKAI-{timestamp}")))
        display_text("Smile...")
        ret, photo = self._cam.read()

        if not ret:
            log.error("Failed to take a photo from WebCam!")
            return None

        cv2.imwrite(ensure_endswith(filepath, '-photo.png'), photo)
        face_files: list[str]= self._detect_faces(photo, filepath)
        log.info(f"WebCam photo taken: '%s'. number of faces detected: %s.", filepath, len(face_files))
        self._store_faces(face_files)

        return filepath

    def _detect_faces(self, photo: numpy.ndarray, filepath: str) -> list[str]:
        """Whether to detect all faces in the photo."""

        # Face detection
        gray_img = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
        faces = self._haarFaceCascade.detectMultiScale(
            gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
        )
        # For each face detected on the photo.
        face_files: list[str] = list()
        for x, y, w, h in faces:
            # Draw a rectangle around the detected faces.
            cv2.rectangle(photo, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cropped_face = photo[y: y + h, x: x + w]
            f_face: str = ensure_endswith(filepath, f'-face-{len(face_files)}.png')
            if cv2.imwrite(f_face, cropped_face):
                face_files.append(f_face)
                log.info("Face file successfully saved: '%s' !", f_face)
            else:
                log.error("Failed to save face file: '%s' !", f_face)

        return face_files

    def _store_faces(self, face_files: list[str]) -> None:
        """Store the faces into the Vector store.
        https://chatgpt.com/c/a5dd43d1-d56c-46fd-8be8-934c97adb4f3
        Ref:.https://github.com/chroma-core/chroma/blob/main/examples/use_with/roboflow/embeddings.ipynb
        """
        data_loader = ImageLoader()
        ibed = imgbeddings()
        persist_dir: str = str(Path.joinpath(PICTURE_DIR, "store"))
        client = chromadb.PersistentClient(path=persist_dir)
        # for next_face in face_files:
        #     if face_img := Image.open(next_face):
        #         embeddings = ibed.to_embeddings(face_img)
        #         print(str(embeddings[0].tolist()))
        collection = client.create_collection(
            name="images_db2",
            embedding_function=ibed.to_embeddings,
            data_loader=data_loader,
            metadata={"hnsw:space": "cosine"}
        )
        print(collection)

    @retry(tries=3, backoff=1)
    def _initialize(self) -> None:
        """Initialize the camera."""
        self._cam = cv2.VideoCapture(0)
        ret, img = self._cam.read()
        log.info("Starting the WebCam device")
        if not (ret and img is not None):
            log.error("Failed to initialize the camera !")
        atexit.register(self._shutdown)

    def _shutdown(self) -> None:
        """Shutdown the camera."""
        if self._cam.isOpened():
            log.info("Shutting down the WebCam device")
            self._cam.release()


assert (camera := Camera().INSTANCE) is not None

if __name__ == "__main__":
    while (done := input("Press [Enter] to take photo")) not in ["e", "q"]:
        camera.capture()
