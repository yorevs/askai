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


@dataclass(frozen=True)
class AIReply:
    """Data class that represents AI replies."""

    message: str = ""
    is_success: bool = True
    is_debug: bool = False
    is_verbose: bool = False
    is_speakable: bool = True

    def __str__(self) -> str:
        return (
            f"Success: {self.is_success}\t"
            f"Debug: {self.is_debug}\t"
            f"Speakable: {self.is_speakable}\t"
            f"Verbose: {self.is_verbose}\t"
            f"Message: {self.message}\t"
        )
