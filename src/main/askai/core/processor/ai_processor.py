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
from abc import ABCMeta
from askai.core.askai_prompt import prompt
from askai.core.model.query_response import QueryResponse
from functools import lru_cache
from hspylib.core.tools.commons import dirname
from hspylib.core.tools.text_tools import camelcase
from importlib import import_module
from os.path import basename
from pathlib import Path
from typing import Dict, Optional, Tuple

import os

from askai.core.support.utilities import hash_text


class AIProcessor(metaclass=ABCMeta):
    """Abstract class that helps implementing AskAI processors."""

    _PROCESSORS: Dict[str, "AIProcessor"] = {}

    @classmethod
    @lru_cache
    def find_query_types(cls) -> str:
        """Search and retrieve all possible query types."""
        q_types = []
        for root, _, files in os.walk(dirname(__file__)):
            procs = list(filter(lambda m: m.endswith("_processor.py") and m != basename(__file__), files))
            for proc in procs:
                proc_name = os.path.splitext(proc)[0]
                proc_pkg = import_module(f"{__package__}.{proc_name}")
                proc_class = getattr(proc_pkg, camelcase(proc_name, capitalized=True))
                proc_inst: "AIProcessor" = proc_class()
                cls._PROCESSORS[proc_inst.processor_id()] = proc_inst
                if proc_inst.query_desc():
                    q_types.append(str(proc_inst))
        return os.linesep.join(q_types)

    @classmethod
    @lru_cache
    def get_by_query_type(cls, query_type: str) -> Optional["AIProcessor"]:
        """Retrieve an AIProcessor by query type.
        :param query_type: The type of the query.
        """
        return next((p for p in cls._PROCESSORS.values() if p.supports(query_type)), None)

    @classmethod
    @lru_cache
    def get_by_name(cls, name: str) -> Optional["AIProcessor"]:
        """Retrieve an AIProcessor by its name.
        :param name: The name of the processor.
        """
        return next((p for p in cls._PROCESSORS.values() if type(p).__name__ == name), None)

    def __init__(self, template_file: str | Path, persona_file: str | Path):
        self._template_file = str(template_file)
        self._persona_file = str(persona_file)
        self._next_in_chain = None

    def __str__(self):
        return f"'{self.query_type()}': {self.query_desc()}"

    @property
    def name(self) -> str:
        return type(self).__name__

    def supports(self, q_type: str) -> bool:
        """Determine if the processor is able to handle a query type.
        :param q_type: The query type.
        """
        return q_type in [self.query_type()]

    def processor_id(self) -> str:
        """Get the processor ID. the resulting ID is a string, composed by the processor name hash."""
        return hash_text(self.__class__.__name__)

    def query_type(self) -> str:
        """Get the query type this processor can handle. By default, it's the name of the processor itself."""
        return self.processor_id()

    def query_desc(self) -> str:
        """Get a description about this processor. When empty, they will not be eligible for auto-select."""
        return ""

    def template(self) -> str:
        return prompt.read_prompt(self._template_file, self._persona_file)

    def next_in_chain(self) -> Optional["AIProcessor"]:
        """Return the next processor in the chain to call. Defaults to None."""
        return self._next_in_chain

    def bind(self, next_in_chain: "AIProcessor"):
        """Bind a processor to be the next in chain."""
        self._next_in_chain = next_in_chain

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        """TODO"""
        ...
