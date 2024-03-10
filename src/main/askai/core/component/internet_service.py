#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.utils
      @file: cache_service.py
   @created: Tue, 16 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
import os
from typing import List, Optional

from hspylib.core.metaclass.singleton import Singleton
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.tools import Tool


class InternetService(metaclass=Singleton):
    """Provide a internet search service used to complete queries that require realtime data.ß"""

    INSTANCE: 'InternetService' = None

    ASKAI_INTERNET_DATA_KEY = "askai-internet-data"

    def __init__(self):
        self._search = GoogleSearchAPIWrapper()
        self._tool = Tool(
            name="google_search", description="Search Google for recent results.", func=self._search.run,
    )

    def _top_results(self, query: str, max_results: int = 5) -> List[str]:
        """TODO"""
        return self._search.results(query, max_results)

    def search(self, query: str) -> Optional[str]:
        """TODO"""
        search_results = self._tool.run(query)
        log.debug(f"Internet search returned: %s", search_results)
        return os.linesep.join(search_results) if isinstance(search_results, list) else search_results


assert (internet := InternetService().INSTANCE) is not None
