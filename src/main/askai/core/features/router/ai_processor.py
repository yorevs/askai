#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.features.router
      @file: ai_engine.py
   @created: Fri, 5 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class AIProcessor(Protocol):
    """Provide an interface for AI processors (routing modes)."""

    def process(self, question: str, **kwargs) -> Optional[str]:
        """Process a user query."""
        ...
