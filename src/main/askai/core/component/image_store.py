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
from askai.core.features.router.tools.vision import image_captioner
from chromadb.api.types import IncludeEnum
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions.open_clip_embedding_function import OpenCLIPEmbeddingFunction
from collections import namedtuple
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.dict_tools import get_or_default
from langchain_community.retrievers.pinecone_hybrid_search import hash_text
from os.path import basename
from pathlib import Path
from torchvision.datasets.folder import is_image_file
from typing import Any, Mapping, Optional, TypeAlias

import askai.core.component.cache_service as cache
import chromadb
import logging as log
import numpy
import os

Metadata: TypeAlias = Mapping[str, str | int | float | bool]

ImageData: TypeAlias = numpy.ndarray[Any, numpy.dtype]

ImageFile = namedtuple('ImageFile', ['img_id', 'img_path', 'img_category', 'img_caption'])

ImageMetadata = namedtuple('ImageMetadata', ['name', 'data', 'uri', 'distance'])


class ImageStore(metaclass=Singleton):
    """Provide an interface to capture WebCam photos."""

    INSTANCE: "ImageStore"

    COLLECTION_NAME: str = "image_store"

    PHOTO_CATEGORY: str = 'photos'

    FACE_CATEGORY: str = 'faces'

    IMPORTS_CATEGORY: str = 'imports'

    @staticmethod
    def sync_folders(with_caption: bool = False, *dirs: AnyPath) -> list[ImageFile]:
        """Load image files from the specified directories."""

        def category() -> str:
            """TODO"""
            cat_str: str
            if dir_path == str(cache.PHOTO_DIR):
                cat_str = store.PHOTO_CATEGORY
            elif dir_path == str(cache.FACE_DIR):
                cat_str = store.FACE_CATEGORY
            else:
                cat_str = store.IMPORTS_CATEGORY
            return cat_str

        img_files: list[ImageFile] = []
        load_dirs: list[str] = [str(p) for p in dirs]
        for (dir_path, dir_names, file_names) in os.walk(cache.PICTURE_DIR):
            if dir_path in load_dirs:
                cat: str = category()
                files: list[str] = list(filter(is_image_file, map(lambda fn: os.path.join(dir_path, fn), file_names)))
                img_files.extend(
                    ImageFile(
                        hash_text(basename(f)), f, cat, image_captioner(f) if with_caption else "No caption"
                    ) for f in files
                )

        return img_files

    def __init__(self):
        self._db_client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._img_collection = self._db_client.get_or_create_collection(
            self.COLLECTION_NAME,
            embedding_function=OpenCLIPEmbeddingFunction(),
            data_loader=ImageLoader()
        )

    @property
    def persist_dir(self) -> Path:
        return Path.joinpath(cache.PICTURE_DIR, self.COLLECTION_NAME)

    @property
    def metadatas(self) -> Optional[list[Metadata]]:
        return self._img_collection.get()['metadatas']

    def enlist(self) -> Optional[list[str]]:
        return [str(mt).replace("'", '"') for mt in self.metadatas]

    def store_image(self, *face_files: ImageFile) -> int:
        """Add the faces into the image store collection."""

        if face_files:
            img_ids = [ff.img_id for ff in face_files]
            img_uris = [ff.img_path for ff in face_files]
            img_metas = [
                {
                    'img_id': ff.img_id,
                    'img_path': ff.img_path,
                    'img_category': ff.img_category,
                    'img_caption': ff.img_caption,
                }
                for ff in face_files
            ]
            self._img_collection.add(ids=img_ids, uris=img_uris, metadatas=img_metas)
            log.info("Face collection increased to: '%d' !", self._img_collection.count())

        return self._img_collection.count()

    def clear_store(self) -> None:
        """Clear the image store collection."""

        log.info("Clearing image store collection: '%s'", self.COLLECTION_NAME)
        self._db_client.delete_collection(self.COLLECTION_NAME)
        self._img_collection = self._db_client.get_or_create_collection(
            self.COLLECTION_NAME,
            embedding_function=OpenCLIPEmbeddingFunction(),
            data_loader=ImageLoader()
        )

    def sync_store(self, with_caption: bool = False) -> int:
        """Synchronize image store collection with the picture folder."""

        log.info("Synchronizing image store folders: '%s', '%s' and '%s'",
                 cache.PHOTO_DIR, cache.FACE_DIR, cache.IMG_IMPORTS_DIR)
        self.clear_store()
        img_files: list[ImageFile] = self.sync_folders(
            with_caption, cache.PHOTO_DIR, cache.FACE_DIR, cache.IMG_IMPORTS_DIR)
        self.store_image(*img_files)

        return len(img_files)

    def query_image(self, query: str, max_results: int = 1) -> list[ImageMetadata]:
        """Query for a photo matching the query."""
        return self.search_image(query, [self.PHOTO_CATEGORY, self.IMPORTS_CATEGORY], max_results)

    def query_face(self, query: str, max_results: int = 1) -> list[ImageMetadata]:
        """Query for a face matching the query."""
        return self.search_image(query, [self.FACE_CATEGORY], max_results)

    def search_image(self, query: str, categories: list[str], max_results: int = 1) -> list[ImageMetadata]:
        """Search for images using natural language."""
        return self._query(max_results, categories=categories, query_texts=[query])

    def search_face(self, photo: ImageData, max_results: int = 1) -> list[ImageMetadata]:
        """Search for faces matching the provided photo using similarity methods."""
        return self._query(max_results, categories=[self.FACE_CATEGORY], query_images=[photo])

    def _query(self, max_results: int = 5, **kwargs) -> list[ImageMetadata]:
        """Query the database for images."""
        result: list[ImageMetadata] = []
        categories: list[str] = kwargs['categories'] or []
        filters: dict[str, Any] = self._categories(categories)
        del kwargs['categories']
        query_results = self._img_collection.query(
            **kwargs,
            n_results=5,
            include=[
                IncludeEnum.documents,
                IncludeEnum.distances,
                IncludeEnum.metadatas,
                IncludeEnum.data,
                IncludeEnum.uris
            ],
            where=filters
        )
        for i in range(len(query_results['ids'][0])):
            if (img_data := get_or_default(query_results['data'][0], i, None)) is None:
                continue
            img_name = query_results['metadatas'][0][i]['img_caption']
            img_path = query_results['metadatas'][0][i]['img_path']
            img_dist = query_results['distances'][0][i]
            result.append(ImageMetadata(img_name, img_data, img_path, img_dist))
        # Sort by distance
        result.sort(key=lambda img: img[3])

        return result[0:max_results]

    def _categories(self, categories: list[str]) -> dict[str, Any]:
        """Build the category filter to query images."""
        return {"$or": [{'img_category': cat} for cat in categories]} \
            if len(categories) > 1 \
            else {'img_category': get_or_default(categories, 0, "")}


assert (store := ImageStore().INSTANCE) is not None
