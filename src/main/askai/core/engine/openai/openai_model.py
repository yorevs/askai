#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.openai
      @file: openai_model.py
   @created: Fri, 12 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.engine.ai_model import AIModel
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.preconditions import check_not_none
from typing import List


class OpenAIModel(Enumeration):
    """Enumeration for the supported OpenAI models. This class implements the AIModel protocol.
    Reference: https://www.pluralsight.com/resources/blog/data/ai-gpt-models-differences
    """

    # ID of the model to use. Currently, only the values below are supported:

    # fmt: off

    GPT_3_5_TURBO           = "gpt-3.5-turbo", 4096
    GPT_4                   = "gpt-4", 8192
    GPT_4_TURBO             = "gpt-4-turbo", 128000
    GPT_4_O                 = "gpt-4o", 128000
    GPT_4_O_MINI            = "gpt-4o-mini", 128000
    O1_PREVIEW              = "o1-preview", 128000
    O1_MINI                 = "o1-mini", 128000

    # fmt: on

    @staticmethod
    def models() -> List["AIModel"]:
        """Get the list of available models for the engine.
        :return: A list of available AI models.
        """
        return [OpenAIModel.of_value(m) for m in OpenAIModel.values()]

    @staticmethod
    def of_name(model_name: str) -> "AIModel":
        """Get the AIModel instance corresponding to the given model name.
        :param model_name: The name of the AI model.
        :return: The corresponding AIModel instance.
        """
        found = next((m for m in OpenAIModel.models() if m.model_name() == model_name.casefold()), None)
        check_not_none(found, '"{}" name does not correspond to a valid "{}" enum', model_name, OpenAIModel.__name__)
        return found

    def __init__(self, model_name: str, token_limit: int):
        self._model_name = model_name
        self._token_limit = token_limit

    def __str__(self):
        return f"{self.model_name()}, {self.token_limit()}k tokens"

    def model_name(self) -> str:
        """Get the official model's name."""
        return self._model_name

    def token_limit(self) -> int:
        """Get the official model tokens limit."""
        return self._token_limit
