#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: query_type.py
   @created: Fri, 23 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from hspylib.core.enums.enumeration import Enumeration


class QueryType(Enumeration):
    """TODO"""

    # fmt: off
    TYPE_1 = "Type-1", False
    TYPE_2 = "Type-2", True
    TYPE_3 = "Type-3", True
    TYPE_4 = "Type-4", True
    TYPE_5 = "Type-5", True
    # fmt: on

    def __init__(self, type_name: str, cacheable: bool):
        self._type_name = type_name
        self._cacheable = cacheable
