#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.protocols
      @file: ai_processor.py
   @created: Fri, 23 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from typing import Protocol

from askai.core.model.query_type import QueryType


class AIProcessor(Protocol):

    def supports(self, q_type: QueryType):
        """TODO"""
        ...

    def process(self) -> bool:
        """TODO"""
        ...

    def next_in_chain(self) -> 'AIProcessor':
        """TODO"""
        ...
