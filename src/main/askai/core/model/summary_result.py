#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: summary_result.py
   @created: Sun, 10 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from dataclasses import dataclass

import json


@dataclass
class SummaryResult:
    """Keep track of the summarization responses."""

    folder: str = None
    glob: str = None
    question: str = None
    answer: str = None

    def __str__(self):
        return f"Summarization results: {json.dumps(self.__dict__, default=lambda obj: obj.__dict__)}"
