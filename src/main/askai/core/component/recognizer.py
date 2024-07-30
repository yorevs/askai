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
import os
from collections import namedtuple
from os.path import basename
from pathlib import Path
from typing import TypeAlias

import chromadb
import numpy
from chromadb.api.types import IncludeEnum
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions.open_clip_embedding_function import OpenCLIPEmbeddingFunction
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.dict_tools import get_or_default
from langchain_community.retrievers.pinecone_hybrid_search import hash_text
from torchvision.datasets.folder import is_image_file

from askai.core.component.cache_service import PICTURE_DIR, PHOTO_DIR, FACE_DIR

ImageData: TypeAlias = numpy.ndarray

ImageFile = namedtuple('ImageFile', ['img_id', 'img_path', 'img_category', 'img_name'])

ImageMetadata = namedtuple('ImageData', ['name', 'data', 'uri', 'distance'])


class Recognizer(metaclass=Singleton):
    """Provide an interface to capture WebCam photos."""

    INSTANCE: "Recognizer"

    COLLECTION_NAME: str = "image_store"

    PHOTO_CATEGORY: str = 'photos'

    FACE_CATEGORY: str = 'faces'

    def __init__(self):
        self._db_client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._img_collection = self._db_client.get_or_create_collection(
            self.COLLECTION_NAME,
            embedding_function=OpenCLIPEmbeddingFunction(),
            data_loader=ImageLoader()
        )

    @property
    def persist_dir(self) -> Path:
        return Path.joinpath(PICTURE_DIR, self.COLLECTION_NAME)

    def store_image(self, *face_files: ImageFile) -> None:
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
            self._img_collection.add(
                ids=img_ids,
                uris=img_uris,
                metadatas=img_metas
            )
            log.info("Face collection increased to: '%d' !", self._img_collection.count())

    def clear_store(self) -> None:
        """TODO"""
        log.info("Clearing image store collection: '%s'", self.COLLECTION_NAME)
        self._db_client.delete_collection(self.COLLECTION_NAME)
        self._img_collection = self._db_client.get_or_create_collection(
            self.COLLECTION_NAME,
            embedding_function=OpenCLIPEmbeddingFunction(),
            data_loader=ImageLoader()
        )

    def sync_store(self) -> int:
        """TODO"""
        log.info("Synchronizing image store folders: '%s' and '%s'", PHOTO_DIR, FACE_DIR)
        self.clear_store()
        img_files: list[ImageFile] = list()
        for (dir_path, dir_names, file_names) in os.walk(PICTURE_DIR):
            if dir_path in [str(PHOTO_DIR), str(FACE_DIR)]:
                files: list[str] = list(filter(is_image_file, map(lambda fn: os.path.join(dir_path, fn), file_names)))
                img_files.extend(
                    ImageFile(
                        hash_text(basename(f)), f,
                        recognizer.PHOTO_CATEGORY if dir_path == str(PHOTO_DIR) else recognizer.FACE_CATEGORY,
                        'Import'
                    ) for f in files
                )
        self.store_image(*img_files)
        return len(img_files)

    def query_face(self, query: str, max_results: int = 1) -> list[ImageMetadata]:
        """Query for a face matching the query."""
        return self.search_image(self.FACE_CATEGORY, max_results, query)

    def query_photo(self, query: str, max_results: int = 1) -> list[ImageMetadata]:
        """Query for a photo matching the query."""
        return self.search_image(self.PHOTO_CATEGORY, max_results, query)

    def search_image(self, category: str, max_results: int, query: str) -> list[ImageMetadata]:
        """Search for images using natural language."""
        return self._query(category, max_results, query_texts=[query])

    def search_face(self, photo: ImageData) -> list[ImageMetadata]:
        """Search for faces matching the provided photo using similarity methods."""
        return self._query(self.FACE_CATEGORY, 1, query_images=[photo])

    def _query(self, category: str, max_results: int, **kwargs) -> list[ImageMetadata]:
        """Query the database for images."""
        result: list[ImageMetadata] = list()
        query_results = self._img_collection.query(
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
