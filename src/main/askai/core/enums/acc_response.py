#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.enums.acc_response
      @file: acc_response.py
   @created: Tue, 23 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from hspylib.core.enums.enumeration import Enumeration
from typing import Literal

import re


class AccResponse(Enumeration):
    """Track and classify accuracy responses based on color classifications. This class provides an enumeration of
    possible accuracy responses, which are typically represented by different colors.
    """

    # fmt: off

    EXCELLENT   = 'Blue'

    GOOD        = 'Green'

    MODERATE    = 'Yellow'

    INCOMPLETE  = 'Orange'

    BAD         = 'Red'

    INTERRUPT   = 'Black'

    # fmt: on

    @classmethod
    def matches(cls, output: str) -> re.Match:
        """Find a match in the given output string.
        :param output: The string to search for a match.
        :return: A match object if a match is found.
        :raises: re.error if an error occurs during the matching process.
        """
        return re.search(cls._re(), output.replace("\n", " "), flags=re.IGNORECASE)

    @classmethod
    def _re(cls) -> str:
        """TODO"""
        return rf"^\$?({'|'.join(cls.values())})[:,-]\s*[0-9]+%\s+(.+)"

    @classmethod
    def strip_code(cls, message: str) -> str:
        """Strip the color code from the message.
        :param message: The message from which to strip color codes.
        :return: The message with color codes removed.
        """
        mat = cls.matches(message)
        return str(mat.group(2)).strip() if mat else message.strip()

    @classmethod
    def of_status(cls, status: str, reasoning: str | None) -> "AccResponse":
        """Create an AccResponse instance based on status and optional reasoning.
        :param status: The status as a string.
        :param reasoning: Optional reasoning for the status, formatted as '<percentage>% <details>'.
        :return: An instance of AccResponse with the given status and reasoning.
        """
        resp = cls.of_value(status.title())
        if reasoning and (mat := re.match(r"(^[0-9]{1,3})%\s+(.*)", reasoning)):
            resp.rate = float(mat.group(1))
            resp.reasoning = mat.group(2)
        return resp

    def __init__(self, color: Literal["Blue", "Green", "Yellow", "Orange", "Red"]):
        self.color = color
        self.reasoning: str | None = None
        self.rate: float | None = None

    def __str__(self):
        details: str = f"{' -> ' + str(self.rate) + '% ' + self.reasoning if self.reasoning else ''}"
        return f"{self.name}{details}"

    @property
    def is_bad(self) -> bool:
        return self in [self.BAD, self.INCOMPLETE]

    @property
    def is_moderate(self) -> bool:
        return self == self.MODERATE

    @property
    def is_good(self) -> bool:
        return self in [self.GOOD, self.EXCELLENT]

    @property
    def is_interrupt(self) -> bool:
        return self == self.INTERRUPT

    def passed(self, threshold: "AccResponse") -> bool:
        """Determine whether the response matches a 'PASS' classification.
        :param threshold: The threshold or criteria used to determine a 'PASS' classification.
        :return: True if the response meets or exceeds the 'PASS' threshold, otherwise False.
        """
        if isinstance(threshold, AccResponse):
            idx_self, idx_threshold = None, None
            for i, v in enumerate(AccResponse.values()):
                if v == self.value:
                    idx_self = i
                if v == threshold.value:
                    idx_threshold = i
            return idx_self is not None and idx_threshold is not None and idx_self <= idx_threshold
        return False
