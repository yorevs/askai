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
    def search_sites(self, query: str, after: str, *urls: str) -> Optional[str]:
        """Search the web using google search API.
        :param after:
        :param query: TODO
        :param urls: TODO
        """
        search_results = ''
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.searching())
        date = f"after: {after}"
        for url in urls:
            site = f"site: {url}"
            log.info("Searching GOOGLE for '%s'  '%s'  '%s'", query, site, date)
            results = self._tool.run(f"{query} + {site} + {date}")
            search_results += str(results)
        log.debug(f"Internet search returned: %s", search_results)
        return os.linesep.join(search_results) if isinstance(search_results, list) else search_results


assert (internet := InternetService().INSTANCE) is not None
