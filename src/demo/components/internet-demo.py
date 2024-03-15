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
from askai.core.component.cache_service import cache
from askai.core.component.internet_service import internet
from askai.core.support.shared_instances import shared
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.tools.commons import log_init, sysout

import logging as log

if __name__ == "__main__":
    log_init("internet-demo.log", level=log.INFO)
    cache.read_query_history()
    sysout("-=" * 40)
    sysout("AskAI Internet Demo")
    sysout("-=" * 40)
    shared.create_engine(engine_name="openai", model_name="gpt-3.5-turbo")
    urls = ["https://www.accuweather.com"]
    sysout(f"READY to search")
    sysout("--" * 40)
    while (query := line_input("You: ")) not in ["exit", "q", "quit"]:
        answer = internet.search_google(query, *urls)
        sysout(f"%GREEN%AI: {answer}")
    cache.save_query_history()
