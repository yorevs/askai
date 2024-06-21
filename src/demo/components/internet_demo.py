#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: demo.components
      @file: internet-demo.py
   @created: Tue, 14 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
from askai.core.component.internet_service import internet
from askai.core.model.search_result import SearchResult
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.tools.commons import sysout
from utils import init_context

import re

if __name__ == "__main__":
    init_context("internet-demo")
    sysout("-=" * 40)
    sysout("AskAI Internet Demo")
    sysout("-=" * 40)
    sysout(f"READY to search")
    sysout("--" * 40)

    while (query := line_input("You: ")) not in ["exit", "q", "quit"]:
        kw: list[str] = re.split("[ ,;]", query)
        sites: list[str] = ["https://www.uol.com.br/"]
        q = SearchResult(query, geo_location.datetime, "news", kw, sites)
        # answer = internet.search_google(q)
        answer = internet.scrap_sites(q)
        sysout(f"%GREEN%AI: {answer}")
        cache.save_query_history()
