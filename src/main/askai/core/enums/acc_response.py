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

import re


class RagResponse(Enumeration):
    """Keep track of the RAG model responses (classifications)."""

    # fmt: off

    EXCELLENT   = 'Blue'

    GOOD        = 'Green'

    MODERATE    = 'Yellow'

    INCOMPLETE  = 'Orange'

    BAD         = 'Red'

    # fmt: on

    @classmethod
    def matches(cls, output: str) -> re.Match:
        return re.search(cls._re(), output.replace("\n", " "), re.IGNORECASE)

    @classmethod
    def _re(cls) -> str:
        return rf"^\$?({'|'.join(cls.values())})[:,-]\s*(.+)"

    @classmethod
    def strip_code(cls, message: str) -> str:
        """Strip the color code from the message"""
        mat = cls.matches(message)
        return str(mat.group(2)).strip() if mat else message.strip()

    @classmethod
    def of_status(cls, status: str) -> "RagResponse":
        return cls.of_value(status.title())

    @property
    def is_bad(self) -> bool:
        return self in [self.BAD, self.INCOMPLETE]

    @property
    def is_moderate(self) -> bool:
        return self == self.MODERATE

    @property
    def is_good(self) -> bool:
        return self in [self.GOOD, self.EXCELLENT]

    def passed(self, threshold: 'RagResponse') -> bool:
        """whether the response matches a 'PASS' classification."""
        if isinstance(threshold, RagResponse):
            idx_self, idx_threshold = None, None
            for i, v in enumerate(RagResponse.values()):
                if v == self.value:
                    idx_self = i
                if v == threshold.value:
                    idx_threshold = i
            return idx_self is not None and idx_threshold is not None and idx_self <= idx_threshold
        return False
