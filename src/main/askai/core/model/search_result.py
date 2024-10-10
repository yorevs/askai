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
from askai.core.component.geo_location import geo_location
from askai.core.support.llm_parser import parse_field, parse_list
from dataclasses import dataclass
from typing import Literal

import json


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
    def parse_response(cls, question: str, response: str) -> "SearchResult":
        """Parse the router's response and convert it into an ActionPlan.
        :param question: The original question or command that was sent to the router.
        :param response: The router's response.
        :return: An instance of ActionPlan created from the parsed response.
        """

        engine: Literal["Google", "Bing"] = parse_field("@engine", response)
        category: str = parse_field("@category", response)
        keywords: list[str] = parse_list("@keywords", response, is_dict=False)
        sites: list[str] = parse_list("@sites", response, is_dict=False)
        filters: list[str] = parse_list("@filters", response, is_dict=False)

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
