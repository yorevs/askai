#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: search_result.py
   @created: Sun, 12 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from dataclasses import dataclass
from typing import List

import json


@dataclass
class SearchResult:
    """Keep track of the internet search responses."""

    question: str = None
    datetime: str = None
    category: str = None
    keywords: List[str] = None
    sites: List[str] = None
    filters: List[str] = None
    response: str = None

    def __str__(self):
        return f"Search Results: {json.dumps(self.__dict__, default=lambda obj: obj.__dict__)}"
