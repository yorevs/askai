#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.model
      @file: ai_reply.py
   @created: Fri, 12 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from dataclasses import dataclass


@dataclass
class AIReply:
    """Data class that represents AI replies."""

    message: str = ""
    is_success: bool = False

    def __str__(self) -> str:
        return f"Success = {self.is_success}\nMessage = {self.message}"
