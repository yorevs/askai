#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: summary_result.py
   @created: Tue, 11 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.core.enums.response_model import ResponseModel
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class ModelResult:
    """Track and store the responses from the selected model. This class is used to encapsulate the model selection
    returned by the LLM, including any relevant data associated with the model's response."""

    mid: str = None
    goal: str = None
    reason: str = None

    @staticmethod
    @lru_cache
    def default() -> "ModelResult":
        """Creates and returns the default ModelResult instance.
        :return: A default ModelResult instance with predefined values.
        """
        return ModelResult(ResponseModel.NEUTRAL.model, "Default model", "Provide the answer as received by the AI")

    @staticmethod
    @lru_cache
    def final_answer() -> "ModelResult":
        """Generates and returns the final answer model result.
        :return: An instance of ModelResult representing the final answer model.
        """
        return ModelResult(
            ResponseModel.FINAL_ANSWER.model, "Final Answer model", "Provide the answer as received by the AI"
        )

    def __str__(self):
        return f"{self.mid} -> {self.reason}"
