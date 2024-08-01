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
    """Keep track of the accuracy responses (color classifications)."""

    # fmt: off

    EXCELLENT   = 'Blue'

    GOOD        = 'Green'

    MODERATE    = 'Yellow'

    INCOMPLETE  = 'Orange'

    BAD         = 'Red'

    # fmt: on

    @classmethod
    def matches(cls, output: str) -> re.Match:
        return re.search(cls._re(), output.replace("\n", " "), flags=re.IGNORECASE)

    @classmethod
    def _re(cls) -> str:
        return rf"^\$?({'|'.join(cls.values())})[:,-]\s*[0-9]+%\s+(.+)"

    @classmethod
    def strip_code(cls, message: str) -> str:
        """Strip the color code from the message"""
        mat = cls.matches(message)
        return str(mat.group(2)).strip() if mat else message.strip()

    @classmethod
    def of_status(cls, status: str, reasoning: str | None) -> "AccResponse":
        resp = cls.of_value(status.title())
        if reasoning and (mat := re.match(r'(^[0-9]{1,3})%\s+(.*)', reasoning)):
            resp.rate = float(mat.group(1))
            resp.reasoning = mat.group(2)
        return resp

    def __init__(self, color: Literal['Blue', 'Green', 'Yellow', 'Orange', 'Red']):
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

    def passed(self, threshold: 'AccResponse') -> bool:
        """whether the response matches a 'PASS' classification."""
        if isinstance(threshold, AccResponse):
            idx_self, idx_threshold = None, None
            for i, v in enumerate(AccResponse.values()):
                if v == self.value:
                    idx_self = i
                if v == threshold.value:
                    idx_threshold = i
            return idx_self is not None and idx_threshold is not None and idx_self <= idx_threshold
        return False
