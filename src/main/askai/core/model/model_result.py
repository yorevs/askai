#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: summary_result.py
   @created: Tue, 11 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class ModelResult:
    """Keep track of the model select responses."""
    mid: str
    goal: str
    reason: str

    @staticmethod
    @lru_cache
    def default() -> 'ModelResult':
        """Return  hte default ModelResult."""
        return ModelResult("GPT_005", "Final Answer", "Provide a direct answer for the user")

    def __str__(self):
        return f"({self.mid})->{self.reason}"
