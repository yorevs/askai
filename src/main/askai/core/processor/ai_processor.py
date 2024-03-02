#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processor
      @file: ai_processor.py
   @created: Fri, 23 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from typing import Protocol, Optional, Tuple

from askai.core.model.query_response import QueryResponse


class AIProcessor(Protocol):

    def supports(self, q_type: str) -> bool:
        """TODO"""
        ...

    def processor_id(self) -> str:
        """TODO"""
        ...

    def query_type(self) -> str:
        """TODO"""
        ...

    def query_desc(self) -> str:
        """TODO"""
        ...

    def template(self) -> str:
        """TODO"""
        ...

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        """TODO"""
        ...

    def next_in_chain(self) -> Optional['AIProcessor']:
        """TODO"""
        ...
