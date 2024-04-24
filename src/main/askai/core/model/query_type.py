#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.model
      @file: query_type.py
   @created: Fri, 12 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from hspylib.core.enums.enumeration import Enumeration


class QueryType(Enumeration):
    """TODO"""

    ANALYSIS_QUERY = "AnalysisQuery"

    COMMAND_QUERY = "CommandQuery"

    GENERIC_QUERY = "GenericQuery"

    INTERNET_QUERY = "InternetQuery"

    OUTPUT_QUERY = "OutputQuery"

    SUMMARY_QUERY = "SummaryQuery"

    def __str__(self):
        return self.value[0]

    @property
    def proc_name(self) -> str:
        return self.value[0].replace("Query", "Processor")
