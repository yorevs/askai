#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.protocols
      @file: ai_reply.py
   @created: Thu, 18 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from typing import Protocol


class AIReply(Protocol):
    """Provide an interface for AI replies."""

    def reply_text(self) -> str:
        """Get the retrieved reply message."""
        ...

    def is_success(self) -> bool:
        """Whether this is a success reply."""
        ...
