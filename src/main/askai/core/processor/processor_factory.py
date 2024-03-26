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
import os
from functools import lru_cache
from importlib import import_module
from os.path import dirname
from typing import Dict, Optional

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import camelcase

from askai.core.processor.processor_base import AIProcessor


class ProcessorFactory(metaclass=Singleton):
    """TODO"""

    _PROCESSORS: Dict[str, AIProcessor] = {}

    """Search and retrieve all possible query types."""
    for root, _, files in os.walk(f"{dirname(__file__)}/instances"):
        procs = list(filter(lambda m: m.endswith("_processor.py"), files))
        for proc in procs:
            proc_name = os.path.splitext(proc)[0]
            proc_pkg = import_module(f"{__package__}.instances.{proc_name}")
            proc_class = getattr(proc_pkg, camelcase(proc_name, capitalized=True))
            proc_inst: AIProcessor = proc_class()
            _PROCESSORS[type(proc_inst).__name__] = proc_inst

    @classmethod
    @lru_cache
    def find_processor(cls, query_type: str) -> Optional[AIProcessor]:
        """Retrieve an AIProcessor by query type.
        :param query_type: The type of the query.
        """
        return next(
            (p for p in cls._PROCESSORS.values() if p.supports(query_type)), None
        )

    @classmethod
    @lru_cache
    def get_by_name(cls, name: str) -> Optional[AIProcessor]:
        """Retrieve an AIProcessor by its name.
        :param name: The name of the processor.
        """
        return next(
            (p for p in cls._PROCESSORS.values() if type(p).__name__ == name), None
        )

    @classmethod
    @lru_cache
    def analysis(cls) -> AIProcessor:
        return cls._PROCESSORS['AnalysisProcessor']

    @classmethod
    @lru_cache
    def command(cls) -> AIProcessor:
        return cls._PROCESSORS['CommandProcessor']

    @classmethod
    @lru_cache
    def generic(cls) -> AIProcessor:
        return cls._PROCESSORS['GenericProcessor']

    @classmethod
    @lru_cache
    def internet(cls) -> AIProcessor:
        return cls._PROCESSORS['InternetProcessor']

    @classmethod
    @lru_cache
    def output(cls) -> AIProcessor:
        return cls._PROCESSORS['OutputProcessor']

    @classmethod
    @lru_cache
    def summary(cls) -> AIProcessor:
        return cls._PROCESSORS['SummaryProcessor']

