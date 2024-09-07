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
from typing import AnyStr

from askai.core.enums.verbosity import Verbosity


@dataclass(frozen=True)
class AIReply:
    """Data class that represents AI replies.
    :param message: The reply message.
    :param is_success: Indicates whether the reply is successful.
    :param is_debug: Indicates whether the reply is for debugging.
    :param verbosity: The verbosity level of the reply.
    :param is_speakable: Indicates whether the reply is speakable.
    """

    message: str = ""
    is_success: bool = True
    is_debug: bool = False
    verbosity: Verbosity = Verbosity.MINIMUM
    is_speakable: bool = True

    def __str__(self) -> str:
        return self.message

    @staticmethod
    def info(message: AnyStr, verbosity: Verbosity = Verbosity.NORMAL, speakable: bool = True) -> "AIReply":
        """Creates an info reply.
        :param message: The reply message.
        :param verbosity: The verbosity level of the reply.
        :param speakable: Indicates whether the reply is speakable.
        :return: An AIReply instance with info settings.
        """
        return AIReply(str(message), True, False, verbosity, speakable)

    @staticmethod
    def error(message: AnyStr) -> "AIReply":
        """Creates an error reply.
        :param message: The reply message.
        :return: An AIReply instance with error settings.
        """
        return AIReply(str(message), False, False, Verbosity.NORMAL, False)

    @staticmethod
    def debug(message: AnyStr) -> "AIReply":
        """Creates a debug reply.
        :param message: The reply message.
        :return: An AIReply instance with debug settings.
        """
        return AIReply(str(message), True, True, Verbosity.NORMAL, False)

    @staticmethod
    def mute(message: AnyStr, verbosity: Verbosity = Verbosity.NORMAL) -> "AIReply":
        """Creates a mute reply.
        :param message: The reply message.
        :param verbosity: The verbosity level of the reply.
        :return: An AIReply instance with mute settings.
        """
        return AIReply(str(message), True, False, verbosity, False)

    @property
    def is_error(self) -> bool:
        """Checks if the reply indicates an error.
        :return: True if the reply is not successful, otherwise False.
        """
        return not self.is_success
