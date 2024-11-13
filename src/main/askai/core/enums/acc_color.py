#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.enums.acc_response
      @file: acc_color.py
   @created: Thu, 26 Sep 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from typing import Literal, TypeAlias
import logging as log

from hspylib.core.enums.enumeration import Enumeration

AccuracyColors: TypeAlias = Literal["Blue", "White", "Blue", "Green", "Yellow", "Red"]


class AccColor(Enumeration):
    """TODO"""

    # fmt: off

    INTERRUPT   = 'Black', -1

    TERMINATE   = 'White',  0

    EXCELLENT   = 'Blue',   1

    GOOD        = 'Green',  2

    MODERATE    = 'Yellow', 3

    BAD         = 'Red',    4

    def __init__(self, color: AccuracyColors, weight: int):
        self._color: AccuracyColors = color
        self._weight: int = weight

    def __eq__(self, other: "AccColor") -> bool:
        return self.val == other.val

    def __lt__(self, other) -> bool:
        return self.val < other.val

    def __le__(self, other) -> bool:
        return self.val <= other.val

    def __gt__(self, other) -> bool:
        return self.val > other.val

    def __ge__(self, other) -> bool:
        return self.val >= other.val

    def __str__(self) -> str:
        return self.color

    @classmethod
    def of_color(cls, color_str: AccuracyColors) -> 'AccColor':
        """Create an AccResponse instance based on status and optional reasoning.
        :param color_str: The color as a string.
        :return: An instance of AccColor with the given color.
        """
        acc_color: tuple[str, int] = next((c for c in cls.values() if c[0] == color_str.title()), None)
        if acc_color and isinstance(acc_color, tuple):
            return cls.of_value(acc_color)
        log.error(str(ValueError(f"'{color_str}'is not a valid AccColor")))
        return AccColor.INTERRUPT

    @property
    def color(self) -> str:
        return self.value[0]

    @property
    def val(self) -> int:
        """Gets the integer value of the verbosity level.
        :return: The integer representation of the verbosity level.
        """
        return int(self.value[1])

    @property
    def is_terminate(self) -> bool:
        return self == self.TERMINATE

    @property
    def is_interrupt(self) -> bool:
        return self == self.INTERRUPT

    @property
    def is_bad(self) -> bool:
        return self == self.BAD

    @property
    def is_moderate(self) -> bool:
        return self == self.MODERATE

    @property
    def is_good(self) -> bool:
        return self in [self.GOOD, self.EXCELLENT]

    def passed(self, threshold: "AccColor") -> bool:
        """Determine whether the response matches a 'PASS' classification.
        :param threshold: The threshold or criteria used to determine a 'PASS' classification.
        :return: True if the response meets or exceeds the 'PASS' threshold, otherwise False.
        """
        if isinstance(threshold, AccColor):
            return self.val <= threshold.val
        return False
