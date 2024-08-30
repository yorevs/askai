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
    """Interface for AI processors, also known as routing modes. This protocol defines the required methods and
    behaviors that AI processors must implement to handle specific routing tasks.
    """

    def process(self, question: str, **kwargs) -> Optional[str]:
        """Process a user query and generate a response.
        :param question: The user's query to be processed.
        :param kwargs: Additional arguments that may be used in the processing.
        :return: The generated response as a string, or None if no response is generated.
        """
        ...
