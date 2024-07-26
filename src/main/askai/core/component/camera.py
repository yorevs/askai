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
from pathlib import Path
from typing import Optional, TypeAlias

import chromadb
import cv2
import numpy
import pause
from chromadb.api.types import IncludeEnum
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions.open_clip_embedding_function import OpenCLIPEmbeddingFunction
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.dict_tools import get_or_default
from hspylib.core.tools.text_tools import ensure_endswith, hash_text
from hspylib.core.zoned_datetime import now_ms
from retry import retry

from askai.__classpath__ import classpath
from askai.core.component.cache_service import PICTURE_DIR
from askai.core.support.utilities import display_text

InputDevice: TypeAlias = tuple[int, str]

ImageFile = namedtuple('ImageFile', ['img_id', 'img_path', 'img_category', 'img_name'])

ImageData = namedtuple('ImageData', ['name', 'data', 'uri', 'distance'])


class Camera(metaclass=Singleton):
    """Provide an interface to record voice using the microphone device."""

    INSTANCE: "Camera"

    RESOURCE_DIR: Path = classpath.resource_path()

    ALG: str = "haarcascade_frontalface_default.xml"

    COLLECTION_NAME: str = "img_db"

    FACE_CATEGORY: str = 'faces'

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
        self._cascPath: Path = Path.joinpath(self.RESOURCE_DIR, self.ALG)
        self._haarFaceCascade = cv2.CascadeClassifier(str(self._cascPath))
        self._db_client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._face_collection = self._db_client.get_or_create_collection(
            self.COLLECTION_NAME,
            embedding_function=OpenCLIPEmbeddingFunction(),
            data_loader=ImageLoader()
        )

    @property
    def persist_dir(self) -> Path:
        return Path.joinpath(PICTURE_DIR, self.COLLECTION_NAME)

    def shot(
        self,
        filename: str | None = None,
        store_photo: bool = True,
        detect_faces: bool = False,
        countdown: int = 0,
    ) -> Optional[tuple[str, numpy.ndarray]]:
        """Capture a WebCam frame (take a photo)."""

        self._initialize()

        if not self._cam.isOpened():
            display_text(f"%HOM%%ED2%Error: Camera is not open!%NC%")
            return None

        timestamp: int = now_ms()
        filepath: str = str(Path.joinpath(PICTURE_DIR, basename(filename or f"ASKAI-{timestamp}"))).strip()

        if countdown > 0:
            self._countdown(countdown)

        ret, photo = self._cam.read()

        if not ret:
            log.error("Failed to take a photo from WebCam!")
            return None

        final_path: str = ensure_endswith(filepath, '-photo.png')
        log.info("WebCam photo taken: '%s'", final_path)

        if store_photo:
            cv2.imwrite(final_path, photo)
            camera._store_image(ImageFile(hash_text(basename(final_path)), final_path, self.PHOTO_CATEGORY, 'Photo'))

        if detect_faces:
            self.detect_faces(photo, filepath)

        return final_path, photo

    def detect_faces(self, photo: numpy.ndarray, filepath: str) -> set[ImageFile]:
        """Whether to detect all faces in the photo."""

        # Face detection
        gray_img = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
        faces = self._haarFaceCascade.detectMultiScale(
            gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
        )
        log.info("Detected faces: %d", len(faces))
        face_files: set[ImageFile] = set()
        # For each face detected on the photo.
        for x, y, w, h in faces:
            # Draw a rectangle around the detected faces.
            cv2.rectangle(photo, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cropped_face = photo[y: y + h, x: x + w]
            f_face: str = str(
                Path.joinpath(PICTURE_DIR, basename(ensure_endswith(filepath, f'-face-{len(face_files)}.png')))
            )
            if cv2.imwrite(f_face, cropped_face):
                face_files.add(ImageFile(hash_text(basename(f_face)), f_face, self.FACE_CATEGORY, 'Face'))
                log.info("Face file successfully saved: '%s' !", f_face)
            else:
                log.error("Failed to save face file: '%s' !", f_face)

        if face_files:
            camera._store_image(*face_files)

        return face_files

    def identify(self) -> Optional[ImageData]:
        """Identify the person in front of the WebCam."""
        _, photo = self.shot("ASKAI-ID-PHOTO", False, False)
        result = self._search_face(photo)
        return get_or_default(result, 0, None)

    def query_face(self, query: str, max_results: int = 1) -> list[ImageData]:
        """Query for a face matching the query."""
        return self._search_image(self.FACE_CATEGORY, max_results, query)

    def query_photo(self, query: str, max_results: int = 1) -> list[ImageData]:
        """Query for a photo matching the query."""
        return self._search_image(self.PHOTO_CATEGORY, max_results, query)

    def _store_image(self, *face_files: ImageFile) -> None:
        """Store the faces into the Vector store."""
        if face_files:
            img_ids = [ff.img_id for ff in face_files]
            img_uris = [ff.img_path for ff in face_files]
            img_metas = [
                {
                    'img_id': ff.img_id,
                    'img_category': ff.img_category,
                    'img_name': ff.img_name,
                    'img_path': ff.img_path
                }
                for ff in face_files
            ]
            self._face_collection.add(
                ids=img_ids,
                uris=img_uris,
                metadatas=img_metas
            )
            log.info("Face collection increased to: '%d' !", self._face_collection.count())

    def _search_image(self, category: str, max_results: int, query: str) -> list[ImageData]:
        """Search for images using natural language."""
        return self._query(category, max_results, query_texts=[query])

    def _search_face(self, photo: numpy.ndarray) -> list[ImageData]:
        """Search for faces matching the provided photo using similarity methods."""
        return self._query(self.FACE_CATEGORY, 1, query_images=[photo])

    def _query(self, category: str, max_results: int, **kwargs) -> list[ImageData]:
        """Query the database for images."""
        result: list[ImageData] = list()
        query_results = self._face_collection.query(
            **kwargs,
            n_results=max_results,
            include=[
                IncludeEnum.documents,
                IncludeEnum.distances,
                IncludeEnum.metadatas,
                IncludeEnum.data,
                IncludeEnum.uris
            ],
            where={'img_category': category.casefold()}
        )
        for i in range(len(query_results['ids'][0])):
            if (img_data := get_or_default(query_results['data'][0], i, None)) is None:
                continue
            img_name = query_results['metadatas'][0][i]['img_name']
            img_path = query_results['metadatas'][0][i]['img_path']
            img_dist = query_results['distances'][0][i]
            result.append(ImageData(img_name, img_data, img_path, img_dist))

        return result

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
