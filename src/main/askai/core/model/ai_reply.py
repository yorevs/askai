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
from typing import AnyStr, Literal, TypeAlias

Verbosity: TypeAlias = Literal[1, 2, 3, 4, 5]


@dataclass(frozen=True)
class AIReply:
    """Data class that represents AI replies."""

    message: str = ""
    is_success: bool = True
    is_debug: bool = False
    verbosity: Verbosity = 1
    is_speakable: bool = True

    def __str__(self) -> str:
        return self.message

    @staticmethod
    def info(message: AnyStr, verbosity: Verbosity = 1, speakable: bool = True) -> "AIReply":
        """TODO"""
        return AIReply(str(message), True, False, verbosity, speakable)

    @staticmethod
    def error(message: AnyStr) -> "AIReply":
        """TODO"""
        return AIReply(str(message), True, False, 1, False)

    @staticmethod
    def debug(message: AnyStr) -> "AIReply":
        """TODO"""
        return AIReply(str(message), True, True, 1, False)

    @staticmethod
    def mute(message: AnyStr, verbosity: Verbosity = 1) -> "AIReply":
        """TODO"""
        return AIReply(str(message), True, False, verbosity, False)

    @property
    def is_error(self) -> bool:
        return not self.is_success
