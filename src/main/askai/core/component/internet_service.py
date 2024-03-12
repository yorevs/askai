#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.component
      @file: internet_service.py
   @created: Sun, 10 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
import os
from functools import lru_cache
from typing import Optional

from hspylib.core.metaclass.singleton import Singleton
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.tools import Tool

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg


class InternetService(metaclass=Singleton):
    """Provide a internet search service to complete queries that require realtime data."""

    INSTANCE: "InternetService" = None

    ASKAI_INTERNET_DATA_KEY = "askai-internet-data"

    def __init__(self):
        self._search = GoogleSearchAPIWrapper()
        self._tool = Tool(
            name="google_search",
            description="Search Google for recent results.",
            func=self._search.run)

    @lru_cache
    def search(self, query: str, *sites: str) -> Optional[str]:
        """Search the web using google search API.
        :param query: TODO
        :param sites: TODO
        """
        search_results = ''
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.searching())
        for url in sites:
            log.info("Searching GOOGLE for '%s'  url: '%s'", query, url)
            results = self._tool.run(f"{query} site: {url}")
            search_results += str(results)
        log.debug(f"Internet search returned: %s", search_results)
        return os.linesep.join(search_results) if isinstance(search_results, list) else search_results


assert (internet := InternetService().INSTANCE) is not None
