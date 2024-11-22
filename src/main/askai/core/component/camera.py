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
from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.audio_player import player
from askai.core.component.cache_service import FACE_DIR, IMG_IMPORTS_DIR, PHOTO_DIR
from askai.core.component.image_store import ImageData, ImageFile, ImageMetadata, store
from askai.core.model.ai_reply import AIReply
from askai.core.model.image_result import ImageResult
from askai.core.router.tools.vision import image_captioner, parse_image_caption
from askai.core.support.utilities import build_img_path
from askai.exception.exceptions import CameraAccessFailure, WebCamInitializationFailure
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.dict_tools import get_or_default
from hspylib.core.tools.text_tools import hash_text
from hspylib.core.zoned_datetime import now_ms
from os.path import basename
from pathlib import Path
from retry import retry
from torchvision.datasets.folder import is_image_file
from typing import Optional, TypeAlias

import atexit
import cv2
import glob
import logging as log
import os.path
import pause
import shutil

InputDevice: TypeAlias = tuple[int, str]


class Camera(metaclass=Singleton):
    """Provide an interface to interact with the webcam. This class offers methods for controlling and accessing the
    webcam's functionality, ensuring that only one instance interacts with the hardware at a time.
    """

    INSTANCE: "Camera"

    RESOURCE_DIR: Path = classpath.resource_path

    # Face-Detection algorithm to be used
    ALG: str = configs.face_detect_alg

    @staticmethod
    def countdown(count: int) -> None:
        """Display a countdown before taking a photo.
        :param count: The number of seconds for the countdown.
        """
        if i := count:
            events.reply.emit(reply=AIReply.mute(msg.smile(i)))
            while (i := (i - 1)) >= 0:
                player.play_sfx("click")
                pause.seconds(1)
                events.reply.emit(reply=AIReply.mute(msg.smile(i)), erase_last=True)
            player.play_sfx("camera-shutter")
            events.reply.emit(reply=AIReply.mute(msg.click()), erase_last=True)

    def __init__(self):
        self._cam = None
        self._alg_path: Path = Path.joinpath(self.RESOURCE_DIR, self.ALG)
        self._face_classifier = cv2.CascadeClassifier(str(self._alg_path))

    @retry(tries=3, backoff=1, delay=1)
    def initialize(self) -> None:
        """Initialize the camera device."""
        if not self._cam or not self._cam.isOpened():
            self._cam = cv2.VideoCapture(0)
            ret, img = self._cam.read()
            log.info("Starting the WebCam device")
            if not (ret and img is not None):
                raise WebCamInitializationFailure("Failed to initialize the WebCam device !")
            else:
                atexit.register(self.shutdown)

    @retry(tries=3, backoff=1, delay=1)
    def shutdown(self) -> None:
        """Shutdown the camera device."""
        if self._cam and self._cam.isOpened():
            log.info("Shutting down the WebCam device")
            self._cam.release()

    def capture(
        self, filename: AnyPath, countdown: int = 3, with_caption: bool = True, store_image: bool = True
    ) -> Optional[tuple[ImageFile, ImageData]]:
        """Capture a webcam frame (take a photo).
        :param filename: The file name for the capturing image.
        :param countdown: The number of seconds for the countdown before capturing the photo (default is 3).
        :param with_caption: Whether to generate a caption for the captured image (default is True).
        :param store_image: Whether to save the captured image to the image store (default is True).
        :return: A tuple containing the image file and image data, or None if the capture fails.
        """

        self.initialize()

        if not self._cam.isOpened():
            events.reply.emit(reply=AIReply.error(msg.camera_not_open()))
            return None

        self.countdown(countdown)

        ret, photo = self._cam.read()
        if not ret:
            raise CameraAccessFailure("Failed to take a photo from WebCam!")

        filename: str = filename or str(now_ms())
        final_path: str = build_img_path(PHOTO_DIR, str(filename), "-PHOTO.jpg")
        if final_path and cv2.imwrite(final_path, photo):
            log.debug("WebCam photo taken: %s", final_path)
            photo_file = ImageFile(
                hash_text(basename(final_path)),
                final_path,
                store.PHOTO_CATEGORY,
                parse_image_caption(image_captioner(final_path)) if with_caption else msg.no_caption(),
            )
            if store_image:
                store.store_image(photo_file)
            events.reply.emit(reply=AIReply.debug(msg.photo_captured(photo_file.img_path)))
            return photo_file, photo

        return None

    def detect_faces(
        self, photo: ImageData, filename: AnyPath = None, with_caption: bool = True, store_image: bool = True
    ) -> tuple[list[ImageFile], list[ImageData]]:
        """Detect all faces in the provided photo.
        :param photo: The image data in which to detect faces.
        :param filename: The file name for the detected face image.(optional).
        :param with_caption: Whether to generate captions for the detected faces (default is True).
        :param store_image: Whether to save the processed images to the image store (default is True).
        :return: A tuple containing a list of image files and a list of image data for the detected faces.
        """

        face_files: list[ImageFile] = []
        face_datas: list[ImageData] = []
        gray_img = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
        faces = self._face_classifier.detectMultiScale(
            gray_img, scaleFactor=configs.scale_factor, minNeighbors=configs.min_neighbors, minSize=configs.min_max_size
        )
        log.debug("Detected faces: %d", len(faces))

        if len(faces) == 0:
            return face_files, face_datas

        filename: str = filename or str(now_ms())
        for x, y, w, h in faces:
            cropped_face: ImageData = photo[y : y + h, x : x + w]
            final_path: str = build_img_path(FACE_DIR, str(filename), f"-FACE-{len(face_files)}.jpg")
            if final_path and cv2.imwrite(final_path, cropped_face):
                result: ImageResult = ImageResult.of(image_captioner(final_path))
                face_file = ImageFile(
                    hash_text(basename(final_path)),
                    final_path,
                    store.FACE_CATEGORY,
                    get_or_default(result.people_description, 0, "<N/A>") if with_caption else msg.no_caption(),
                )
                face_files.append(face_file)
                face_datas.append(cropped_face)
                log.debug("Face file successfully saved: '%s' !", final_path)
            else:
                raise CameraAccessFailure(f"Failed to save face file: '{final_path}'!")

        if store_image:
            store.store_image(*face_files)

        return face_files, face_datas

    def identify(self, countdown: int = 0, max_distance: float = configs.max_id_distance) -> Optional[ImageMetadata]:
        """Identify the person in front of the webcam.
        :param countdown: The number of seconds for the countdown before capturing an identification the photo
                          (default is 0).
        :param max_distance: The maximum allowable distance for face recognition accuracy (default is
                          configs.max_id_distance).
        :return: Metadata about the identified person, or None if identification fails.
        """
        _, photo = self.capture("ASKAI-ID", countdown, False, False)
        _ = self.detect_faces(photo, "ASKAI-ID", False, False)
        result = list(filter(lambda p: p.distance <= max_distance, store.find_by_similarity(photo)))
        id_data: ImageMetadata = next(iter(result), None)
        log.info("WebCam identification request: %s", id_data or "<No-One>")

        return id_data

    def import_images(
        self, pathname: AnyPath, detect_faces: bool = False, with_caption: bool = True, store_image: bool = True
    ) -> tuple[int, ...]:
        """Import image files into the image collection.
        :param pathname: The path or glob pattern of the images to be imported.
        :param detect_faces: Whether to detect faces in the imported images (default is False).
        :param with_caption: Whether to generate captions for the imported images (default is True).
        :param store_image: Whether to save the processed images to the image store (default is True).
        :return: A tuple containing the number of images successfully imported, and the number of detected faces.
        """

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
                img_path,
                store.IMPORTS_CATEGORY,
                parse_image_caption(image_captioner(img_path)),
            )

        def _do_import(*img_path: str) -> None:
            log.debug("Importing images: %s", img_path)
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


assert (camera := Camera().INSTANCE) is not None
