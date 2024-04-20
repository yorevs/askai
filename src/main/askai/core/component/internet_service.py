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
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import PERSIST_DIR
from askai.core.component.geo_location import geo_location
from askai.core.component.summarizer import summarizer
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.search_result import SearchResult
from askai.core.support.langchain_support import lc_llm, load_document
from askai.core.support.shared_instances import shared
from functools import lru_cache
from googleapiclient.errors import HttpError
from hspylib.core.metaclass.singleton import Singleton
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_community.document_loaders.async_html import AsyncHtmlLoader
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.tools import Tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional

import logging as log
import re


class InternetService(metaclass=Singleton):
    """Provide a internet search service to complete queries that require realtime data."""

    INSTANCE: "InternetService" = None

    ASKAI_INTERNET_DATA_KEY = "askai-internet-data"

    @staticmethod
    def scrap_sites(search: SearchResult) -> Optional[str]:
        """Scrap a web page and summarize it's contents.
        :param search: The AI search parameters.
        """
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.searching())
        if len(search.sites) > 0:
            query = "+".join(search.keywords)
            log.info("Scrapping sites: '%s'", str(", ".join(search.sites)))
            documents: List[Document] = load_document(AsyncHtmlLoader, list(search.sites))
            if len(documents) > 0:
                texts: List[Document] = summarizer.text_splitter.split_documents(documents)
                v_store = Chroma.from_documents(texts, lc_llm.create_embeddings(), persist_directory=str(PERSIST_DIR))
                retriever = RetrievalQA.from_chain_type(
                    llm=lc_llm.create_model(), chain_type="stuff", retriever=v_store.as_retriever()
                )
                search_results = retriever.invoke({"query": query})
                return search_results["result"]
        return None

    @staticmethod
    def _build_query(search: SearchResult) -> str:
        """TODO"""
        query = ""
        # Gather the sites to be used in te search.
        if search.sites:
            query += f" {' OR '.join(['site:' + url for url in search.sites])}"
        # Weather is a filter that does not require any other search parameter.
        if search.filters and any(f.find("weather:") >= 0 for f in search.filters):
            return re.sub(r"^weather:(.*)", r'weather:"\1"', " AND ".join(search.filters))
        # We want to find pages containing the exact name of the person.
        if search.filters and any(f.find("people:") >= 0 for f in search.filters):
            return f" ${query} intext:\"{' + '.join([f.split(':')[1] for f in search.filters])}\" "
        # Make the search query using the provided keywords.
        if search.keywords:
            query += f" {' + '.join(search.keywords)} "
        return query

    def __init__(self):
        self._google = GoogleSearchAPIWrapper()
        self._tool = Tool(name="google_search", description="Search Google for recent results.", func=self._google.run)
        self._text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=25)

    @lru_cache
    def template(self) -> str:
        return prompt.read_prompt("search-prompt")

    @lru_cache
    def refine_template(self) -> str:
        return prompt.read_prompt("refine-search-prompt")

    def search_google(self, search: SearchResult) -> Optional[str]:
        """Search the web using google search API.
        Google search operators: https://ahrefs.com/blog/google-advanced-search-operators/
        :param search: The AI search parameters.
        """
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.searching())
        search.sites = search.sites if len(search.sites) > 0 else ["google.com", "bing.com"]
        try:
            query = self._build_query(search).strip()
            log.info("Searching Google for '%s'", query)
            ctx = str(self._tool.run(query))
            llm_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
            context: List[Document] = [Document(ctx)]
            chain = create_stuff_documents_chain(
                lc_llm.create_chat_model(temperature=Temperature.DATA_ANALYSIS.temp), llm_prompt
            )
            output = chain.invoke({"query": search.question, "context": context})
        except HttpError as err:
            output = msg.fail_to_search(str(err))

        return self.refine_search(search.question, output, search.sites) if output else None

    def refine_search(self, question: str, context: str, sites: list[str]) -> str:
        """Refines the text retrieved by the search engine."""
        refine_prompt = PromptTemplate.from_template(self.refine_template()).format(
            idiom=shared.idiom, sources=sites, location=geo_location.location,
            datetime=geo_location.datetime, context=context, question=question
        )
        log.info("STT::[QUESTION] '%s'", context)
        llm = lc_llm.create_chat_model(temperature=Temperature.CREATIVE_WRITING.temp)

        return llm.invoke(refine_prompt).content


assert (internet := InternetService().INSTANCE) is not None
