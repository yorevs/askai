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
import os
from functools import lru_cache
from importlib import import_module
from os.path import basename, dirname
from typing import Protocol, Optional, Tuple

from hspylib.core.tools.text_tools import camelcase


@lru_cache
def get_query_types() -> str:
    q_types = []
    for root, _, files in os.walk(dirname(__file__)):
        procs = list(filter(lambda m: m.endswith("_processor.py") and m != basename(__file__), files))
        for proc in procs:
            proc_name = os.path.splitext(proc)[0]
            p_mod = import_module(f"{__package__}.{proc_name}")
            p_class = getattr(p_mod, camelcase(proc_name, capitalized=True))
            q_types.append(str(p_class()))
    return os.linesep.join(q_types)


class AIProcessor(Protocol):

    def supports(self, q_type: str) -> bool:
        """TODO"""
        ...

    def processor_id(self):
        """TODO"""
        ...

    def query_name(self) -> str:
        """TODO"""
        ...

    def query_desc(self) -> str:
        """TODO"""
        ...

    def prompt(self) -> str:
        """TODO"""
        ...

    def process(self) -> Tuple[bool, str]:
        """TODO"""
        ...

    def prev_in_chain(self) -> Optional['AIProcessor']:
        """TODO"""
        ...

    def next_in_chain(self) -> Optional['AIProcessor']:
        """TODO"""
        ...
