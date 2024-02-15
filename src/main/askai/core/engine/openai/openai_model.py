#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.openai
      @file: openai_model.py
   @created: Fri, 12 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from askai.core.engine.protocols.ai_model import AIModel
from hspylib.core.enums.enumeration import Enumeration
from typing import List


class OpenAIModel(Enumeration):
    """Enumeration for the supported OpenAi models. Implements the AIModel protocol."""

    # ID of the model to use. Currently, only the values below are supported:

    # fmt: off
    GPT_3_5_TURBO           = "gpt-3.5-turbo"
    GPT_3_5_TURBO_16K       = "gpt-3.5-turbo-16k"
    GPT_3_5_TURBO_1106      = "gpt-3.5-turbo-1106"
    GPT_3_5_TURBO_0301      = "gpt-3.5-turbo-0301"
    GPT_3_5_TURBO_0613      = "gpt-3.5-turbo-0613"
    GPT_3_5_TURBO_16K_0613  = "gpt-3.5-turbo-16k-0613"
    GPT_4                   = "gpt-4"
    GPT_4_1106_PREVIEW      = "gpt-4-1106-preview"
    GPT_4_0314              = "gpt-4-0314"
    GPT_4_0613              = "gpt-4-0613"
    GPT_4_32K               = "gpt-4-32k"
    GPT_4_32K_0314          = "gpt-4-32k-0314"
    GPT_4_32K_0613          = "gpt-4-32k-0613"
    GPT_4_VISION_PREVIEW    = "gpt-4-vision-preview"
    # fmt: on

    def model_name(self) -> str:
        """Get the official model's name."""
        return self.value

    @staticmethod
    def models() -> List["AIModel"]:
        return [m.of_value() for m in OpenAIModel.values()]
