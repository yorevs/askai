#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: ai_vision.py
   @created: Tue, 3 Sep 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from hspylib.core.metaclass.classpath import AnyPath
from typing import Protocol, Literal


class AIVision(Protocol):
    """Provide an interface for AI vision."""

    def caption(
        self,
        filename: AnyPath,
        load_dir: AnyPath | None,
        query: str | None = None,
        image_type: Literal["photo", "screenshot"] = "photo",
    ) -> str:
        """Generate a caption for the provided image.
        :param filename: File name of the image for which the caption is to be generated.
        :param load_dir: Optional directory path for loading related resources.
        :param query: Optional question about details of the image.
        :param image_type: The type of the image to be captioned; one of 'photo' or 'screenshot'.
        :return: A string containing the generated caption.
        """
        ...
