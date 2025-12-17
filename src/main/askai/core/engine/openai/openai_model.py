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

Copyright (c) 2024, AskAI
"""

from askai.core.engine.ai_model import AIModel
from hspylib.core.enums.enumeration import Enumeration
from typing import List


class OpenAIModel(Enumeration):
    """Enumeration for the supported OpenAI models. This class implements the AIModel protocol.
    Reference: https://www.pluralsight.com/resources/blog/data/ai-gpt-models-differences
    """

    # ID of the model to use. Currently, only the values below are supported:
    # Note: These prices are estimates based on historical trends and reported updates as of December 2025.
    # Actual OpenAI API pricing evolves frequently (e.g., GPT-4o updated to ~$5/$15).
    # Reasoning models (o-series) may have additional costs for thinking tokens.
    # Always verify the latest official rates at https://openai.com/api/pricing/ as models like GPT-5.2 and
    # newer variants have taken precedence. Legacy models may be deprecated or repriced.

    # fmt: off
    GPT_5 = "gpt-5", 1_000_000  # Input: $1.25 / 1M, Output: $10.00 / 1M (estimated for flagship series)
    GPT_5_CHAT = "gpt-5-chat", 1_000_000  # Input: $1.25 / 1M, Output: $10.00 / 1M
    GPT_5_MINI = "gpt-5-mini", 1_000_000  # Input: $0.25 / 1M, Output: $2.00 / 1M
    GPT_5_NANO = "gpt-5-nano", 1_000_000  # Input: $0.05 / 1M, Output: $0.40 / 1M
    GPT_5_1 = "gpt-5.1", 1_000_000  # Input: $1.25 / 1M, Output: $10.00 / 1M
    GPT_5_1_CHAT = "gpt-5.1-chat", 1_000_000  # Input: $1.25 / 1M, Output: $10.00 / 1M
    GPT_5_1_MINI = "gpt-5.1-mini", 1_000_000  # Input: $0.25 / 1M, Output: $2.00 / 1M
    GPT_5_1_NANO = "gpt-5.1-nano", 1_000_000  # Input: $0.20 / 1M, Output: $0.80 / 1M
    GPT_5_2 = "gpt-5.2", 1_000_000  # Input: $1.75 / 1M, Output: $14.00 / 1M
    GPT_5_2_CHAT = "gpt-5.2-chat", 1_000_000  # Input: $1.75 / 1M, Output: $14.00 / 1M
    GPT_5_2_MINI = "gpt-5.2-mini", 1_000_000  # Input: $0.25 / 1M, Output: $2.00 / 1M
    GPT_5_2_NANO = "gpt-5.2-nano", 1_000_000  # Input: $0.20 / 1M, Output: $0.80 / 1M
    GPT_4 = "gpt-4", 8192  # Legacy; refer to current pricing for equivalents
    GPT_4_TURBO = "gpt-4-turbo", 128000  # Legacy; refer to current pricing for equivalents
    GPT_4_O = "gpt-4o", 128000  # Input: $5.00 / 1M, Output: $15.00 / 1M (updated late 2025)
    GPT_4_O_MINI = "gpt-4o-mini", 128000  # Input: $0.15 / 1M, Output: $0.60 / 1M (or similar; check latest)
    GPT_4_1 = "gpt-4.1", 1_000_000  # Input: $3.00 / 1M, Output: $12.00 / 1M (approximate)
    GPT_4_1_MINI = "gpt-4.1-mini", 1_000_000  # Input: $0.80 / 1M, Output: $3.20 / 1M (approximate)
    GPT_4_1_NANO = "gpt-4.1-nano", 1_000_000  # Input: $0.20 / 1M, Output: $0.80 / 1M
    GPT_4_5 = "gpt-4.5", 128000  # Legacy/preview; refer to current equivalents
    O1 = "o1", 128000  # Input: $15.00 / 1M, Output: $60.00 / 1M (reasoning tokens extra)
    O1_PREVIEW = "o1-preview", 128000  # Similar to o1
    O1_MINI = "o1-mini", 128000  # Input: $3.00 / 1M, Output: $12.00 / 1M (approximate)
    O1_PRO = "o1-pro", 128000  # Higher pricing variant
    O3 = "o3", 128000  # Input: $2.00 / 1M, Output: $8.00 / 1M (post price drop)
    O3_MINI = "o3-mini", 128000  # Input: $1.10 / 1M, Output: $4.40 / 1M
    O3_MINI_HIGH = "o3-mini-high", 128000  # Input: ~$4.00 / 1M, Output: ~$16.00 / 1M (higher effort)
    O3_PRO = "o3-pro", 128000  # Input: $20.00 / 1M, Output: $80.00 / 1M
    O4_MINI = "o4-mini", 128000  # Input: $1.10 / 1M, Output: $4.40 / 1M (base)
    O4_MINI_HIGH = "o4-mini-high", 128000  # Input: $4.00 / 1M, Output: $16.00 / 1M (higher effort)
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
        if found is None:
            raise ValueError(f'"{model_name}" name does not correspond to a valid "{OpenAIModel.__name__}" enum')

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
