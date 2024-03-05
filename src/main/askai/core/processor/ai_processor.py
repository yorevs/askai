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
import os
from abc import ABCMeta
from functools import lru_cache
from importlib import import_module
from os.path import basename
from typing import Optional, Tuple, Dict

from hspylib.core.tools.commons import dirname
from hspylib.core.tools.text_tools import camelcase

from askai.core.model.query_response import QueryResponse


class AIProcessor(metaclass=ABCMeta):
    """Abstract class that helps implementing AskAI processors."""

    _PROCESSORS: Dict[str, 'AIProcessor'] = {}

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
                proc_inst = proc_class()
                cls._PROCESSORS[proc_inst.processor_id()] = proc_inst
                q_types.append(str(proc_inst))
        return os.linesep.join(q_types)

    @classmethod
    @lru_cache
    def get_by_query_type(cls, query_type: str) -> Optional['AIProcessor']:
        """Retrieve an AIProcessor by query type.
        :param query_type: The type of the query.
        """
        return next((p for p in cls._PROCESSORS.values() if p.supports(query_type)), None)

    @classmethod
    @lru_cache
    def get_by_name(cls, name: str) -> Optional['AIProcessor']:
        """Retrieve an AIProcessor by its name.
        :param name: The name of the processor.
        """
        return next((p for p in cls._PROCESSORS.values() if type(p).__name__ == name), None)

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
