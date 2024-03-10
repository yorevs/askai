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
from typing import Optional

from hspylib.core.metaclass.singleton import Singleton
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.tools import Tool

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg


class InternetService(metaclass=Singleton):
    """Provide a internet search service used to complete queries that require realtime data.ß"""

    INSTANCE: 'InternetService' = None

    ASKAI_INTERNET_DATA_KEY = "askai-internet-data"

    def __init__(self):
        self._search = GoogleSearchAPIWrapper()
        self._tool = Tool(
            name="google_search",
            description="Search Google for recent results.",
            func=self._top_results,
    )

    def _top_results(self, query: str, max_results: int = 5) -> str:
        """TODO"""
        ln = os.linesep
        results = self._search.results(query, max_results)
        return ln.join([f"{i}- {r['snippet']}" for i, r in enumerate(results)])

    def search(self, query: str) -> Optional[str]:
        """TODO"""
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.searching())
        search_results = self._tool.run(query)
        log.debug(f"Internet search returned: %s", search_results)
        return os.linesep.join(search_results) if isinstance(search_results, list) else search_results


assert (internet := InternetService().INSTANCE) is not None


if __name__ == '__main__':
    res = internet.search('Qual o proximo jogo do flamengo em 2024')
    print(res)
