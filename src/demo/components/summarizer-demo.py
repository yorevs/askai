#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib
   @package: demo.components
      @file: summarizer-demo.py
   @created: Tue, 14 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import os
import logging as log
from typing import List

from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.tools.commons import sysout, log_init

from askai.core.component.cache_service import cache
from askai.core.component.summarizer import summarizer
from askai.core.support.shared_instances import shared


if __name__ == '__main__':
    log_init("summarizer-demo.log", level=log.INFO)
    cache.read_query_history()
    sysout("-=" * 40)
    sysout("AskAI Summarizer Demo")
    sysout("-=" * 40)
    folder, glob = os.getenv("HOME") + '/HomeSetup', '**/*.md'
    shared.create_engine(engine_name='openai', model_name='gpt-3.5-turbo')
    sysout(f"%GREEN%Summarizing: {folder}/{glob} ...")
    summarizer.generate(folder, glob)
    sysout(f"READY to answer")
    sysout("--" * 40)
    while (query := line_input("You: ")) not in ['exit', 'q', 'quit']:
        results: List[str] = [f"%GREEN%AI: {r.answer}" for r in summarizer.query(query)]
        list(map(sysout, results))
    cache.save_query_history()
