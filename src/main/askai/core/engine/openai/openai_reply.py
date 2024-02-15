#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.openai
      @file: openai_reply.py
   @created: Fri, 12 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""

from askai.core.engine.protocols.ai_reply import AIReply


class OpenAIReply(AIReply):
    """Data class that represent AI replies."""

    def __init__(self, message: str, is_success: bool):
        self._message = message
        self._is_success = is_success

    @property
    def message(self) -> str:
        return self._message

    def reply_text(self) -> str:
        """Get the retrieved reply message."""
        return self._message

    def is_success(self) -> bool:
        """Whether this is a success reply."""
        return self._is_success
