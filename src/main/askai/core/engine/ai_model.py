#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: ai_model.py
   @created: Fri, 5 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from typing import Protocol


class AIModel(Protocol):
    """Provide an interface for AI models."""

    def model_name(self) -> str:
        """Get the official model's name."""
        ...

    def token_limit(self) -> int:
        """Get the official model tokens limit."""
        ...
