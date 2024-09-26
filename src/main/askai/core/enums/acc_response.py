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
import os
from dataclasses import dataclass

from askai.core.enums.acc_color import AccColor, AccuracyColors
from askai.core.support.utilities import parse_field
from hspylib.core.tools.text_tools import ensure_endswith


@dataclass(frozen=True)
class AccResponse:
    """Track and classify accuracy responses based on color classifications. This class provides an enumeration of
    possible accuracy responses, which are typically represented by different colors.
    """

    acc_color: AccColor
    accuracy: float
    reasoning: str
    tips: str

    @classmethod
    def parse_response(cls, response: str) -> "AccResponse":
        """TODO"""

        # FIXME: Remove log the response
        with open("/Users/hjunior/Desktop/acc-response-resp.txt", "w") as f_bosta:
            f_bosta.write(response + os.linesep)
            f_bosta.flush()

        # Parse fields
        acc_color: AccColor = AccColor.of_color(parse_field("@color", response))
        accuracy: float = float(parse_field("@accuracy", response).strip("%"))
        reasoning: str = parse_field("@reasoning", response)
        tips: str = parse_field("@tips", response)

        return AccResponse(acc_color, accuracy, reasoning, tips)

    def __str__(self):
        return f"{self.status} -> {self.details}"

    @property
    def color(self) -> AccuracyColors:
        return self.acc_color.color

    @property
    def status(self) -> str:
        return f"{self.color}, {str(self.accuracy)}%"

    @property
    def details(self) -> str:
        return f"{ensure_endswith(self.reasoning, '.')} {'**' + self.tips + '**' if self.tips else ''}"

    @property
    def is_interrupt(self) -> bool:
        """TODO"""
        return self.acc_color.is_interrupt

    def is_pass(self, threshold: AccColor) -> bool:
        """TODO"""
        return self.acc_color.passed(threshold)
