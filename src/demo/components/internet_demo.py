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

   Copyright (c) 2024, AskAI
"""
import os

import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
from askai.core.component.internet_service import internet
from askai.core.model.search_result import SearchResult
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.tools.commons import sysout
from utils import init_context

import re


def serapi_search(query: str, max_pages: int = 3) -> str:
    params = {
        "engine": "google",
        "q": query,
        "num": max_pages,
        "api_key": os.getenv("SERPAPI_KEY"),
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    ret_text: list[str] = []

    for item in results.get("organic_results", [])[:max_pages]:
        url = item.get("link")
        title = item.get("title")
        print(f"\n# {title}\nURL: {url}")

        try:
            html = requests.get(url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            text = " ".join(s.strip() for s in soup.stripped_strings)
            ret_text.append(text[:1000])  # first 1000 chars preview
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    return os.linesep.join(ret_text)


if __name__ == "__main__":
    init_context("internet-demo")
    sysout("-=" * 40)
    sysout("AskAI Internet Demo")
    sysout("-=" * 40)
    sysout(f"READY to search")
    sysout("--" * 40)

    while (question := line_input("You: ")) not in ["exit", "q", "quit"]:
        kw: list[str] = re.split("[ ,;]", question)
        sites: list[str] = ["https://flamengo.com.br/"]
        q = SearchResult(question, geo_location.datetime, "news", kw, sites)
        # answer = internet.google_search(q)
        answer = internet.scrap_sites(q)
        # answer = serapi_search(qq)
        sysout(f"%GREEN%AI: {answer}")
        cache.save_input_history()
