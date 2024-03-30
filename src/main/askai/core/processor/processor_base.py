#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processor
      @file: processor_base.py
   @created: Fri, 23 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from askai.core.model.processor_response import ProcessorResponse
from typing import Optional, Protocol, Tuple


class AIProcessor(Protocol):
    """Abstract class that helps implementing AskAI processors."""

    def supports(self, query_type: str) -> bool:
        """Determine if the processor is able to handle a query type.
        :param query_type: The query type.
        """
        ...

    def next_in_chain(self) -> Optional["AIProcessor"]:
        """Return the next processor in the chain to call. Defaults to None."""
        ...

    def bind(self, next_in_chain: "AIProcessor") -> None:
        """Bind a processor to be the next in chain."""
        ...

    def process(self, query_response: ProcessorResponse) -> Tuple[bool, Optional[str]]:
        """Process the query response."""
        ...

    def name(self) -> str:
        """Return the processor name."""
        ...

    def description(self) -> str:
        """Get a description about this processor."""
        ...

    def template(self) -> str:
        """Return the processor template text."""
        ...
