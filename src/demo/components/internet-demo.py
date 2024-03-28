#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib
   @package: demo.components
      @file: internet-demo.py
   @created: Tue, 14 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
import re

from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.tools.commons import log_init, sysout

from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
from askai.core.component.internet_service import internet
from askai.core.model.search_result import SearchResult
from askai.core.support.shared_instances import shared

if __name__ == "__main__":

    log_init("internet-demo.log", level=log.INFO)
    cache.read_query_history()
    sysout("-=" * 40)
    sysout("AskAI Internet Demo")
    sysout("-=" * 40)
    shared.create_engine(engine_name="openai", model_name="gpt-3.5-turbo")
    sysout(f"READY to search")
    sysout("--" * 40)

    while (query := line_input("You: ")) not in ["exit", "q", "quit"]:
        kw: list[str] = re.split('[ ,;]', query)
        sites: list[str] = ['accuweather.com', 'weather.com']
        q = SearchResult(query, geo_location.now, kw, sites)
        answer = internet.search_google(q)
        sysout(f"%GREEN%AI: {answer}")
    cache.save_query_history()
