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
import logging as log
from collections import namedtuple
from os.path import basename
from pathlib import Path
from typing import Optional

import chromadb
import cv2
from chromadb.api.types import IncludeEnum
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions.open_clip_embedding_function import OpenCLIPEmbeddingFunction
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.dict_tools import get_or_default
from hspylib.core.tools.text_tools import hash_text

from askai.__classpath__ import classpath
from askai.core.component.cache_service import PICTURE_DIR, FACE_DIR
from askai.core.component.camera import ImageData, ImageFile, camera
from askai.core.support.utilities import build_img_path

ImageMetadata = namedtuple('ImageData', ['name', 'data', 'uri', 'distance'])


class Recognizer(metaclass=Singleton):
    """Provide an interface to capture WebCam photos."""

    INSTANCE: "Recognizer"

    FACE_CATEGORY: str = 'faces'

    RESOURCE_DIR: Path = classpath.resource_path()

    ALG: str = "haarcascade_frontalface_default.xml"

    COLLECTION_NAME: str = "image_store"

    def __init__(self):
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

    def detect_faces(self, photo: ImageData, filename: str) -> tuple[list[ImageFile], list[ImageData]]:
        """Whether to detect all faces in the photo."""

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
                    face_file = ImageFile(hash_text(basename(final_path)), final_path, self.FACE_CATEGORY, 'Face')
                    face_files.append(face_file)
                    face_datas.append(cropped_face)
                    log.info("Face file successfully saved: '%s' !", final_path)
                else:
                    log.error("Failed to save face file: '%s' !", final_path)

        return face_files, face_datas

    def recognize(self) -> Optional[ImageMetadata]:
        """Recognize the person in front of the WebCam."""
        _, photo = camera.capture("ASKAI-ID-PHOTO", False)
        _ = self.detect_faces(photo, "ASKAI-ID-FACE")
        result = self._search_face(photo)
        return next(iter(result), None)

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

    def query_face(self, query: str, max_results: int = 1) -> list[ImageMetadata]:
        """Query for a face matching the query."""
        return self._search_image(self.FACE_CATEGORY, max_results, query)

    def query_photo(self, query: str, max_results: int = 1) -> list[ImageMetadata]:
        """Query for a photo matching the query."""
        return self._search_image(camera.PHOTO_CATEGORY, max_results, query)

    def _search_image(self, category: str, max_results: int, query: str) -> list[ImageMetadata]:
        """Search for images using natural language."""
        return self._query(category, max_results, query_texts=[query])

    def _search_face(self, photo: ImageData) -> list[ImageMetadata]:
        """Search for faces matching the provided photo using similarity methods."""
        return self._query(self.FACE_CATEGORY, 1, query_images=[photo])

    def _query(self, category: str, max_results: int, **kwargs) -> list[ImageMetadata]:
        """Query the database for images."""
        result: list[ImageMetadata] = list()
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
            result.append(ImageMetadata(img_name, img_data, img_path, img_dist))

        return result


assert (recognizer := Recognizer().INSTANCE) is not None
