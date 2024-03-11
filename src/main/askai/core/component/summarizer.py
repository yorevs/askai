#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.component
      @file: summarizer.py
   @created: Mon, 11 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty


class Summarizer(metaclass=Singleton):
    """Provide a summarization service to complete queries that require summarization."""

    INSTANCE: "Summarizer" = None

    ASKAI_SUMMARY_DATA_KEY = "askai-summary-data"

    def generate(self, paths: List[str | Path]) -> Optional[str]:
        """TODO"""
        results: List[str] = []
        for path in paths:
            results.append(self._summarize_file(str(path)))
        return os.linesep.join(results) if len(results) > 0 else None

    @lru_cache
    def _summarize_file(self, filepath: str) -> str:
        """TODO"""
        check_argument(file_is_not_empty(filepath))
        summary = ''
        return summary


assert (summarizer := Summarizer().INSTANCE) is not None
