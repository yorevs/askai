#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.component
      @file: internet_service.py
   @created: Sun, 10 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from askai.__classpath__ import API_KEYS
from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.ai_reply import AIReply
from askai.core.model.search_result import SearchResult
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from collections import defaultdict
from googleapiclient.errors import HttpError
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.zoned_datetime import now
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter
from openai import APIError
from typing import List

import logging as log
import re


class InternetService(metaclass=Singleton):
    """Provide an internet search service to complete queries that require real-time data. This service allows for the
    retrieval of up-to-date information from the web, enabling queries that depend on current data.
    """

    INSTANCE: "InternetService"

    ASKAI_INTERNET_DATA_KEY = "askai-internet-data"

    # fmt: off
    CATEGORY_ICONS = {
        "Weather": "",
        "Sports": "醴",
        "News": "",
        "Celebrities": "",
        "People": "",
        "Programming": "",
        "Travel": "",
        "General": "",
        "Maps": "",
    }

    SITE_ICONS = defaultdict(str, {
        "linkedin.com": "",
        "github.com": "",
        "instagram.com": "",
        "x.com": "X",
        "twitter.com": "",
        "stackoverflow.com": "",
        "facebook.com": "",
        "youtube.com": "",
        "amazon.com": "",
        "apple.com": "",
        "docker.com": "",
        "dropbox.com": "",
        "google.com": "",
        "search.google.com": "",
        "paypal.com": "",
        "wikipedia.org": "荒",
        "reddit.com": "",
        "ubuntu.com": "",
        "fedora.com": "",
    })
    # fmt: on

    @classmethod
    def _url_to_icon(cls, url: str) -> str:
        """TODO"""
        return url.replace(url, cls.SITE_ICONS[url]) if cls.SITE_ICONS[url] else url

    @classmethod
    def wrap_response(cls, terms: str, output: str, search: SearchResult) -> str:
        """Format and wrap the search response based on the search terms, output, and method used.
        :param terms: The search terms used in the query.
        :param output: The raw output or results from the search.
        :param search: The search result.
        :return: A formatted string that encapsulates the search response.
        """
        re_site: str = r"site:([a-zA-Z0-9._%+-]+(?:\.[a-zA-Z]{2,})+)"
        sites: list = re.findall(re_site, terms)
        terms: str = re.sub(r"\s{2,}", " ", re.sub(r"OR", "", re.sub(re_site, "", terms)))
        sources: str = " ".join(sorted([f"{cls._url_to_icon(s):<2}".strip() or s for s in sites], key=len))
        # fmt: off
        return (
            f"Your {search.engine.title()} search has returned the following results:"
            f"\n\n{output}\n\n---\n\n"
            f"`{cls.CATEGORY_ICONS[search.category]:<2}{search.category}`  "
            f"**Sources:** *{sources}*  "
            f"**Access:** {geo_location.location} - *{now('%B %d, %Y')}*\n\n"
            f">   Terms: {terms} \n")
        # fmt: on

    @staticmethod
    def _build_google_query(search: SearchResult) -> str:
        """Build a Google Search query from the provided search parameters.
        :param search: The AI search parameters encapsulated in a SearchResult object.
        :return: A string representing the constructed Google Search query.
        """
        # The order of conditions is important here, as the execution may stop early if a condition is met.
        google_query = ""
        defaults: list[str] = []
        # fmt: off
        match search.category.casefold():
            case "people":
                defaults = ["linkedin.com", "github.com", "instagram.com", "facebook.com"]
                if any((f.find("intext:") >= 0 for f in search.filters)):
                    google_query = (
                        "background OR current work OR achievements "
                        f'{next((f for f in search.filters if f.startswith("intext:")), None)}'
                    )
            case "weather":
                defaults = ["weather.com", "accuweather.com", "weather.gov"]
                if any((f.find("weather:") >= 0 for f in search.filters)):
                    google_query = (
                        f"{now('%B %d %Y')}"
                        f'{next((f for f in search.filters if f.startswith("weather:")), None)}'
                    )
            case "programming":
                defaults = ["stackoverflow.com", "github.com"]
            case "general":
                defaults = ["google.com", "bing.com", "duckduckgo.com", "ask.com"]
            case _:
                if search.keywords:
                    # Gather the sites to be used in the search.
                    google_query = f"{' OR '.join(set(sorted(search.keywords)))}"
        # fmt: on
        sites = f"{' OR '.join(set('site:' + url for url in search.sites + defaults))}"

        return f"{google_query} {sites}"

    def __init__(self):
        self._google: GoogleSearchAPIWrapper | None = None
        self._tool: Tool | None = None
        self._text_splitter: TextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=configs.chunk_size, chunk_overlap=configs.chunk_overlap
        )

    @property
    def refine_template(self) -> str:
        return prompt.read_prompt("refine-search")

    def google_search(self, search: SearchResult) -> str:
        """Search the web using the Google Search API. This method utilizes advanced Google search operators to refine
        and execute the search.
        Reference: https://ahrefs.com/blog/google-advanced-search-operators/
        :param search: The AI search parameters encapsulated in a SearchResult object.
        :return: A refined string containing the search results.
        """
        # Lazy initialization to allow GOOGLE_API_KEY be optional.
        if not self._google:
            API_KEYS.ensure("GOOGLE_API_KEY", "google_search")
            self._google = GoogleSearchAPIWrapper(k=10, google_api_key=API_KEYS.GOOGLE_API_KEY)
            self._tool = Tool(
                name="google_search", description="Search Google for recent results.", func=self._google.run
            )
        events.reply.emit(reply=AIReply.info(msg.searching()))
        terms: str = self._build_google_query(search).strip()
        question: str = re.sub(r"(\w+:)*|((\w+\.\w+)*)", "", terms, flags=re.DOTALL | re.MULTILINE)
        try:
            log.info("Searching Google for '%s'", terms)
            events.reply.emit(reply=AIReply.debug(msg.final_query(terms)))
            results: list[str] = str(self._tool.run(terms, verbose=configs.is_debug)).split(" ")
            refine_prompt = PromptTemplate.from_template(self.refine_template).format(
                idiom=shared.idiom, sources=search.sites, location=geo_location.location, datetime=geo_location.datetime
            )
            llm_prompt = ChatPromptTemplate.from_messages([("system", refine_prompt), ("human", "{question}")])
            docs: List[Document] = [Document(d) for d in results]
            chain = create_stuff_documents_chain(
                lc_llm.create_chat_model(temperature=Temperature.COLDEST.temp), llm_prompt
            )
            output = chain.invoke({"question": question, "context": docs})
        except (HttpError, APIError) as err:
            return msg.fail_to_search(str(err))

        return self.wrap_response(terms, output, search)


assert (internet := InternetService().INSTANCE) is not None
