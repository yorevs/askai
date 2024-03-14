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
from typing import Optional, List

from hspylib.core.metaclass.singleton import Singleton
from langchain.chains import load_summarize_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders.async_html import AsyncHtmlLoader
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_text_splitters import CharacterTextSplitter

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.support.langchain_support import lc_llm, load_document


class InternetService(metaclass=Singleton):
    """Provide a internet search service to complete queries that require realtime data."""

    INSTANCE: "InternetService" = None

    ASKAI_INTERNET_DATA_KEY = "askai-internet-data"

    @staticmethod
    def scrap_sites(*sites: str) -> Optional[str]:
        """TODO"""
        log.info("Scrapping sites: '%s'", str(sites))
        docs: List[Document] = load_document(AsyncHtmlLoader, *sites)
        chain = load_summarize_chain(lc_llm.create_chat_model(), chain_type="stuff")
        search_results = chain.invoke(docs)
        return search_results['output_text']

    def __init__(self):
        self._google = GoogleSearchAPIWrapper()
        self._tool = Tool(
            name="google_search",
            description="Search Google for recent results.",
            func=self._google.run)

    def search_google(self, query: str, *sites: str) -> Optional[str]:
        """Search the web using google search API.
        :param query: The google search query string.
        :param sites: The sites you want google to search for.
        """
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.searching())
        if len(sites) > 0:
            log.info("Searching GOOGLE for '%s'  url: '%s'", query, str(sites))
            search_results: str = ''
            for url in sites:
                search_results += str(self._tool.run(f"{query} site: {url}"))
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            docs: List[Document] = [Document(page_content=x) for x in text_splitter.split_text(search_results)]
            prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
            chain = create_stuff_documents_chain(lc_llm.create_chat_model(), prompt)
            search_results = chain.invoke({"query": query, "context": docs})
            return search_results

        return None


assert (internet := InternetService().INSTANCE) is not None
