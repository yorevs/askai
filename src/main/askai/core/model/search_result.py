#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: search_result.py
   @created: Sun, 12 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import json
import os
from dataclasses import dataclass
from typing import Literal

from askai.core.component.geo_location import geo_location
from askai.core.support.llm_parser import parse_field, parse_list


@dataclass
class SearchResult:
    """Track and store responses from internet searches.
    This class encapsulates the results returned from an internet search, including any relevant data
    associated with the search response.
    """

    question: str = None
    engine: Literal["Google", "Bing"] = None
    category: str = None
    keywords: list[str] = None
    sites: list[str] = None
    filters: list[str] = None
    response: str = None
    datetime: str = geo_location.datetime

    @classmethod
    def parse_response(cls, question: str, query_response: str) -> "SearchResult":
        """TODO"""

        # FIXME: Remove log the response
        with open("/Users/hjunior/Desktop/search-result-resp.txt", "w") as f_bosta:
            f_bosta.write(query_response + os.linesep)
            f_bosta.flush()

        # Parse fields
        engine: Literal["Google", "Bing"] = parse_field("@engine", query_response)
        category: str = parse_field("@category", query_response)
        keywords: list[str] = parse_list("@keywords", query_response, is_dict=False)
        sites: list[str] = parse_list("@sites", query_response, is_dict=False)
        filters: list[str] = parse_list("@filters", query_response, is_dict=False)

        return SearchResult(question, engine, category, keywords, sites, filters)

    def __str__(self):
        return f"Search Results: {json.dumps(self.__dict__, default=lambda obj: obj.__dict__)}"

    def __eq__(self, other: "SearchResult") -> bool:
        """TODO"""
        return (
            self.category == other.category
            and self.keywords == other.keywords
            and self.sites == other.sites
            and self.filters == other.filters
        )

    def build(self) -> str:
        """TODO"""
        return f"{self.keywords} {self.sites} {self.filters}"
