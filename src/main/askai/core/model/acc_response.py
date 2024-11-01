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
from askai.core.enums.acc_color import AccColor, AccuracyColors
from askai.core.support.llm_parser import parse_field
from dataclasses import dataclass
from hspylib.core.tools.text_tools import ensure_endswith
from pathlib import Path


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
        """Parse the LLM response and convert it into an AccResponse.
        :param response: The LLM response.
        :return: An instance of AccResponse created from the parsed response.
        """
        Path(Path.home() / "acc-resp.txt").write_text(response)

        acc_color: AccColor = AccColor.of_color(parse_field("@color", response))
        accuracy: float = float(parse_field("@accuracy", response).strip("%"))
        reasoning: str = parse_field("@reasoning", response)
        tips: str = parse_field("@tips", response)

        return AccResponse(acc_color, accuracy, reasoning, tips)

    def __str__(self):
        return f"{self.status} -> {self.details}"

    def __eq__(self, other: "AccResponse") -> bool:
        """TODO"""
        return (
            self.acc_color == other.acc_color
            and self.accuracy == other.accuracy
            and self.reasoning == other.reasoning
            and self.tips == other.tips
        )

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
        return self.acc_color.is_interrupt

    @property
    def is_terminate(self) -> bool:
        return self.acc_color.is_terminate

    def is_pass(self, threshold: AccColor) -> bool:
        """Determine whether the response matches a 'PASS' classification.
        :param threshold: The threshold or criteria used to determine a 'PASS' classification.
        :return: True if the response meets or exceeds the 'PASS' threshold, otherwise False.
        """
        return self.acc_color.passed(threshold)
