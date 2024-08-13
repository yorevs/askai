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
import glob
import logging as log
import os.path
import shutil
from os.path import basename
from pathlib import Path
from typing import Optional, TypeAlias

import cv2
import pause
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import hash_text
from retry import retry
from torchvision.datasets.folder import is_image_file

from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.component.cache_service import FACE_DIR, PHOTO_DIR, IMG_IMPORTS_DIR
from askai.core.component.image_store import ImageData, ImageFile, ImageMetadata, store
from askai.core.features.router.tools.vision import image_captioner
from askai.core.support.utilities import build_img_path, display_text

InputDevice: TypeAlias = tuple[int, str]


class Camera(metaclass=Singleton):
    """Provide an interface to capture WebCam photos."""

    INSTANCE: "Camera"

    RESOURCE_DIR: Path = classpath.resource_path()

    ALG: str = configs.face_detect_alg

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

    def capture(
        self,
        filename: str,
        countdown: int = 3,
        with_caption: bool = True,
        store_image: bool = True
    ) -> Optional[tuple[ImageFile, ImageData]]:
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

        final_path: str = build_img_path(PHOTO_DIR, filename, '-PHOTO.jpg')
        if final_path and cv2.imwrite(final_path, photo):
            photo_file = ImageFile(
                hash_text(basename(final_path)), final_path, store.PHOTO_CATEGORY,
                image_captioner(final_path) if with_caption else "No caption"
            )
            if store_image:
                store.store_image(photo_file)
            log.info("WebCam photo captured: '%s'", photo_file)
            return photo_file, photo

        return None

    def detect_faces(
        self,
        photo: ImageData,
        filename: str | None = None,
        with_caption: bool = True,
        store_image: bool = True
    ) -> tuple[list[ImageFile], list[ImageData]]:
        """Detect all faces in the photo."""

        face_files: list[ImageFile] = []
        face_datas: list[ImageData] = []
        gray_img = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
        faces = self._haarFaceCascade.detectMultiScale(
            gray_img,
            scaleFactor=configs.scale_factor,
            minNeighbors=configs.min_neighbors,
            minSize=configs.min_size
        )
        log.info("Detected faces: %d", len(faces))

        if len(faces) == 0:
            return face_files, face_datas

        for x, y, w, h in faces:
            cropped_face: ImageData = photo[y: y + h, x: x + w]
            final_path: str = build_img_path(FACE_DIR, filename, f'-FACE-{len(face_files)}.jpg')
            if final_path and cv2.imwrite(final_path, cropped_face):
                face_file = ImageFile(
                    hash_text(basename(final_path)), final_path, store.FACE_CATEGORY,
                    image_captioner(final_path) if with_caption else "No caption"
                )
                face_files.append(face_file)
                face_datas.append(cropped_face)
                log.info("Face file successfully saved: '%s' !", final_path)
            else:
                log.error("Failed to save face file: '%s' !", final_path)

        if store_image:
            store.store_image(*face_files)

        return face_files, face_datas

    def import_images(
        self,
        pathname: AnyPath,
        detect_faces: bool = False,
        with_caption: bool = True,
        store_image: bool = True
    ) -> tuple[int, ...]:
        """TODO"""

        img_datas: list[ImageData] = []
        img_files: list[ImageFile] = []
        faces: list[ImageFile] = []

        def _import_file(src_path: str) -> str:
            dest_path: str = os.path.join(IMG_IMPORTS_DIR, basename(src_path))
            shutil.copyfile(src_path, dest_path)
            return dest_path

        def _read_file(img_path: str) -> ImageFile:
            return ImageFile(
                hash_text(basename(img_path)),
                img_path, store.IMPORTS_CATEGORY,
                image_captioner(img_path) if with_caption else "No caption"
            )

        def _do_import(*img_path: str) -> None:
            log.info("Importing images: %s", img_path)
            import_paths: list[str] = list(map(_import_file, img_path))
            list(map(img_files.append, map(_read_file, import_paths)))
            list(map(img_datas.append, map(cv2.imread, import_paths)))

        if os.path.isfile(pathname):
            _do_import(pathname)
        elif os.path.isdir(pathname):
            _do_import(*list(filter(is_image_file, glob.glob(os.path.join(pathname, "*.*")))))
        else:
            _do_import(*glob.glob(pathname))

        if img_files:
            if store_image:
                store.store_image(*img_files)
            if detect_faces:
                data: ImageData
                file: ImageFile
                for data, file in zip(img_datas, img_files):
                    face_file, _ = self.detect_faces(data, file.img_path, with_caption, store_image)
                    faces.extend(face_file)

        return len(img_files), len(faces)

    def identify(self, max_distance: float = configs.max_id_distance) -> Optional[ImageMetadata]:
        """Identify the person in front of the WebCam."""

        _, photo = self.capture("ASKAI-ID", 0, False, False)
        _ = self.detect_faces(photo, "ASKAI-ID", False, False)
        result = list(filter(lambda p: p.distance <= max_distance, store.search_face(photo)))

        return next(iter(result), None)

    @retry(tries=3, backoff=1, delay=1)
    def _initialize(self) -> None:
        """Initialize the camera device."""
        # Init the WebCam.
        if not self._cam or not self._cam.isOpened():
            self._cam = cv2.VideoCapture(0)
            ret, img = self._cam.read()
            log.info("Starting the WebCam device")
            if not (ret and img is not None):
                log.error("Failed to initialize the WebCam device !")
            else:
                atexit.register(self._shutdown)

    @retry(tries=3, backoff=1, delay=1)
    def _shutdown(self) -> None:
        """Shutdown the camera device."""
        if self._cam and self._cam.isOpened():
            log.info("Shutting down the WebCam device")
            self._cam.release()


assert (camera := Camera().INSTANCE) is not None
