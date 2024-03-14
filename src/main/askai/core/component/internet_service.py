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
from askai.core.support.langchain_support import lc_llm, load_document


class InternetService(metaclass=Singleton):
    """Provide a internet search service to complete queries that require realtime data."""

    INSTANCE: "InternetService" = None

    ASKAI_INTERNET_DATA_KEY = "askai-internet-data"

    @staticmethod
    def scrap_sites(query: str, *sites: str) -> Optional[str]:
        """Scrap a web page and summarize it's contents."""
        log.info("Scrapping sites: '%s'", str(sites))
        documents: List[Document] = load_document(AsyncHtmlLoader, list(sites))
        if len(documents) > 0:
            texts: List[Document] = summarizer.text_splitter.split_documents(documents)
            v_store = Chroma.from_documents(texts, lc_llm.create_embeddings(), persist_directory=str(PERSIST_DIR))
            retriever = RetrievalQA.from_chain_type(
                llm=lc_llm.create_model(), chain_type="stuff", retriever=v_store.as_retriever())
            search_results = retriever.invoke({"query": query})
            return search_results['result']
        return None

    def __init__(self):
        self._google = GoogleSearchAPIWrapper()
        self._tool = Tool(name="google_search", description="Search Google for recent results.", func=self._google.run)
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=10, separators=[" ", ", ", "\n"])

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
            prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
            chain = create_stuff_documents_chain(lc_llm.create_chat_model(), prompt)
            return chain.invoke({"query": query, "context": search_results})

        return None


assert (internet := InternetService().INSTANCE) is not None
