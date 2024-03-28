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
import os
from typing import List, Optional

from hspylib.core.metaclass.singleton import Singleton
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_community.document_loaders.async_html import AsyncHtmlLoader
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.component.cache_service import PERSIST_DIR
from askai.core.component.summarizer import summarizer
from askai.core.model.search_result import SearchResult
from askai.core.support.langchain_support import lc_llm, load_document


class InternetService(metaclass=Singleton):
    """Provide a internet search service to complete queries that require realtime data."""

    INSTANCE: "InternetService" = None

    ASKAI_INTERNET_DATA_KEY = "askai-internet-data"

    @staticmethod
    def scrap_sites(search: SearchResult) -> Optional[str]:
        """Scrap a web page and summarize it's contents.
        :param search: The AI search parameters.
        """
        query = '+'.join(search.keywords)
        if len(search.sites) > 0:
            log.info("Scrapping sites: '%s'", str(', '.join(search.sites)))
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

    def __init__(self):
        self._google = GoogleSearchAPIWrapper()
        self._tool = Tool(name="google_search", description="Search Google for recent results.", func=self._google.run)
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=8, separators=[" ", ", ", os.linesep]
        )

    def search_google(self, search: SearchResult) -> Optional[str]:
        """Search the web using google search API.
        Google search operators: https://ahrefs.com/blog/google-advanced-search-operators/
        :param search: The AI search parameters.
        """
        if len(search.sites) > 0:
            search_results: List[Document] = []
            query = self._build_query(search.keywords, search.filters, search.sites)
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.searching())
            log.info("Searching GOOGLE for '%s'  url: '%s'", query, str(', '.join(search.sites)))
            content = str(self._tool.run(query))
            search_results.append(Document(content))
            prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
            chain = create_stuff_documents_chain(lc_llm.create_chat_model(), prompt)
            return chain.invoke({"query": query, "context": search_results})

        return None

    def _build_query(self, keywords: List[str], filters: List[str], sites: List[str]) -> str:
        """TODO"""
        query = ''
        # Weather is a filter that does not require any other search parameter.
        if filters and any(f.find("weather:") >= 0 for f in filters):
            return ' AND '.join(filters)
        if sites:
            query += ' OR '.join(['site:' + url for url in sites])
        if filters and any(f.find("people:") >= 0 for f in filters):
            query += f" intext:\"{' + '.join([f.split(':')[1] for f in filters])}\" "
        if keywords:
            query += ' + '.join(keywords)
        return query


assert (internet := InternetService().INSTANCE) is not None
