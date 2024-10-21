#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.enums.routing_model
      @file: response_model.py
   @created: Tue, 11 Jun 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from hspylib.core.enums.enumeration import Enumeration

import logging as log
import os


class ResponseModel(Enumeration):
    """Enumeration representing the model used to provide the final answer to the user.
    This class defines the different models that can be used in the routing process to generate and deliver the
    final response.
    """

    # fmt: on

    NEUTRAL = ("ASK_000", "Select this model when no other model fits.")

    # ASSISTIVE_TECH_HELPER
    ASSISTIVE_TECH_HELPER = "ASK_001", (
        "Select this model when you receive requests for **assistive technologies**, such as **speech-to-text**"
    )

    # TERMINAL_COMMAND
    TERMINAL_COMMAND = "ASK_002", (
        "Select this model for executing shell commands, managing terminal operations, listing folder contents, "
        "reading files, and manipulating system resources directly through the command line interface."
    )

    # CONTENT_MASTER
    CONTENT_MASTER = "ASK_003", (
        "Select this model exclusively for creating, generating, and saving any type of content, including text, code, "
        "images, and others. This model should always be used when the task involves generating or saving content."
    )

    # TEXT_ANALYZER
    TEXT_ANALYZER = "ASK_004", (
        "Select this model for extracting and processing information from within individual documents and files "
        "located at the user file system, focusing on text or content analysis within a single file."
    )

    # DATA_ANALYSIS
    DATA_ANALYSIS = "ASK_005", (
        "Select this model for analyzing datasets, performing statistical analysis, and generating reports. Media "
        "Management and Playback: Select this model for organizing, categorizing, and playing multimedia content."
    )

    # CHAT_MASTER
    CHAT_MASTER = "ASK_006", ("Select this model for providing conversational responses or engaging in general chat.")

    # MEDIA_MANAGEMENT_AND_PLAYBACK
    MEDIA_MANAGEMENT_AND_PLAYBACK = "ASK_007", (
        "Select this model for organizing, categorizing, and playing multimedia content."
    )

    # IMAGE_PROCESSOR
    IMAGE_PROCESSOR = "ASK_008", (
        "Select this model for image captioning, face recognition, and visual analysis tasks."
    )

    # SUMMARIZE_AND_QUERY
    SUMMARIZE_AND_QUERY = "ASK_009", (
        "Select this model upon receiving an explicit user request for 'summarization of files and folders'."
    )

    # WEB_FETCH
    WEB_FETCH = "ASK_010", ("Select this model for retrieving information about current events from the web.")

    # WELL_KNOWN
    FINAL_ANSWER = "ASK_011", (
        "Select this model to respond to well-known queries, where you database is enough to "
        "provide a clear and accurate answer."
    )

    # fmt: on

    @classmethod
    def of_model(cls, model_id: str) -> "ResponseModel":
        """Return the ResponseModel instance that matches the given model ID.
        :param model_id: The ID of the model to retrieve.
        :return: The ResponseModel instance corresponding to the specified model ID.
        :raises ValueError: If no matching ResponseModel is found.
        """
        for v in cls.values():
            if v[0] == model_id:
                return cls.of_value(v)

    @classmethod
    def enlist(cls, separator: str = os.linesep) -> str:
        """Return a list of selectable models as a formatted string.
        :param separator: The separator used to delimit the models in the list (default is the system's line separator).
        :return: A string containing the list of selectable models, separated by the specified separator.
        """
        model_list: str = separator.join(f"{v[0]}: {v[1]}" for v in cls.values())
        log.debug("Routing Models: %s", model_list)
        return model_list

    def __str__(self):
        return f"{self.name}::{self.model}"

    def __repr__(self):
        return str(self)

    @property
    def model(self) -> str:
        return self.value[0]

    @property
    def description(self) -> str:
        return self.value[1]
