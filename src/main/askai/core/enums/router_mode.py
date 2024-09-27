#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.enums.router_mode
      @file: router_mode.py
   @created: Tue, 24 Jun 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_configs import configs
from askai.core.features.processors.ai_processor import AIProcessor
from askai.core.features.processors.qna import qna
from askai.core.features.processors.qstring import qstring
from askai.core.features.processors.rag import rag
from askai.core.features.processors.task_splitter import splitter
from askai.core.features.processors.chat import chat
from hspylib.core.enums.enumeration import Enumeration
from typing import Optional


class RouterMode(Enumeration):
    """Enumeration of available router modes used to determine the type of response provided to the user. This class
    defines the different modes that the router can operate in, each affecting how answers are generated and delivered.
    """

    # fmt: off

    TASK_SPLIT = "Task Splitter",               "", splitter

    QNA = "Questions & Answers",                "", qna

    QSTRING = "Non-Interactive",                "", qstring

    RAG = "Retrieval-Augmented-Generation",     "ﮐ", rag

    CHAT = "Taius Chat",                        "", chat

    # fmt: on

    @classmethod
    def modes(cls) -> list[str]:
        """Return a list containing all available agent modes.
        :return: A list of available agent modes as strings.
        """
        return RouterMode.names()

    @staticmethod
    def default() -> "RouterMode":
        """Return the default routing mode.
        :return: The default RouterMode instance.
        """
        return RouterMode.TASK_SPLIT if configs.is_interactive else RouterMode.QSTRING

    @classmethod
    def of_name(cls, name: str) -> "RouterMode":
        """Retrieve the RouterMode instance corresponding to the given name.
        :param name: The name of the router mode to retrieve.
        :return: The RouterMode instance that matches the given name.
        :raises ValueError: If no matching RouterMode is found.
        """
        return cls[name] if name.casefold() != "default" else cls.default()

    def __str__(self):
        return f"{self.icon}  {self.name}"

    def __eq__(self, other: "RouterMode") -> bool:
        return self.name == other.name

    @property
    def name(self) -> str:
        return self.value[0]

    @property
    def icon(self) -> str:
        return self.value[1]

    @property
    def processor(self) -> AIProcessor:
        return self.value[2]

    @property
    def is_default(self) -> bool:
        return self == RouterMode.default()

    def process(self, question: str, **kwargs) -> Optional[str]:
        """Invoke the processor associated with the current mode to handle the given question.
        :param question: The question to be processed.
        :param kwargs: Additional arguments to be passed to the processor.
        :return: The processed response as a string, or None if no response is generated.
        """
        return self.processor.process(question, **kwargs)
