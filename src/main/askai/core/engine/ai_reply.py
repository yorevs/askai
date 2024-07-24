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
    """Data class that represent AI replies."""

    message: str = None
    is_success: bool = None

    def __str__(self):
        return f"Success = {self.is_success}  \nMessage = {self.message}"
