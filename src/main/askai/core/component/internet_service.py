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
from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.component.summarizer import summarizer
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.search_result import SearchResult
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from googleapiclient.errors import HttpError
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.zoned_datetime import now
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.utils import Output
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List

import bs4
import logging as log
import re


class InternetService(metaclass=Singleton):
    """Provide a internet search service to complete queries that require realtime data."""

    INSTANCE: "InternetService"

    ASKAI_INTERNET_DATA_KEY = "askai-internet-data"

    @staticmethod
    def _build_google_query(search: SearchResult) -> str:
        """Build a Google Search query from search parameters.
        :param search: The AI search parameters.
        """
        query = ""
        # Gather the sites to be used in te search.
        if search.sites:
            query += f" {' OR '.join(['site:' + url for url in search.sites])}"
        # Weather is a filter that does not require any other search parameter.
        if search.filters and any(f.find("weather:") >= 0 for f in search.filters):
            return query + ' ' + re.sub(r"^weather:(.*)", r'weather:"\1"', " AND ".join(search.filters))
        # We want to find pages containing the exact name of the person.
        if search.filters and any(f.find("people:") >= 0 for f in search.filters):
            return query + ' ' + f" intext:\"{'+'.join([f.split(':')[1] for f in search.filters])}\" "
        # Make the search query using the provided keywords.
        if search.keywords:
            query = f"{' '.join(search.keywords)} {query} "

        return query

    @staticmethod
    def wrap_response(terms: str, output: str, sites: list[str]) -> str:
        return (
            "Your search returned the following:\n"
            f"\n{output}\n"
            f"\n---"
            f"\nSources: {', '.join(sites)}\n"
            f"\n* Accessed: {geo_location.location} {now('%d %B, %Y')}*"
            f"\n>  Terms: {terms}\n"
        )

    def __init__(self):
        self._google = GoogleSearchAPIWrapper()
        self._tool = Tool(
            name="google_search", description="Search Google for recent results.",
            func=self._google.run
        )
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=configs.chunk_size, chunk_overlap=configs.chunk_overlap)

    def refine_template(self) -> str:
        return prompt.read_prompt("refine-search")

    def search_google(self, search: SearchResult) -> str:
        """Search the web using google search API.
        Google search operators: https://ahrefs.com/blog/google-advanced-search-operators/
        :param search: The AI search parameters.
        """
        events.reply.emit(message=msg.searching())
        search.sites = search.sites or ["google.com", "bing.com", "duckduckgo.com", "ask.com"]
        terms = self._build_google_query(search).strip()
        try:
            log.info("Searching Google for '%s'", terms)
            events.reply.emit(message=msg.final_query(terms), verbosity="debug")
            ctx = str(self._tool.run(terms))
            llm_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
            context: List[Document] = [Document(ctx)]
            chain = create_stuff_documents_chain(
                lc_llm.create_chat_model(temperature=Temperature.CREATIVE_WRITING.temp), llm_prompt
            )
            output = chain.invoke({"query": search.question, "context": context})
        except HttpError as err:
            output = msg.fail_to_search(str(err))

        return self.refine_search(search.question, output, terms, search.sites)

    def scrap_sites(self, search: SearchResult) -> str:
        """Scrap a web page and summarize it's contents.
        :param search: The AI search parameters.
        """
        events.reply.emit(message=msg.scrapping())
        if len(search.sites) > 0:
            log.info("Scrapping sites: '%s'", str(", ".join(search.sites)))
            loader = WebBaseLoader(
                web_paths=search.sites,
                bs_kwargs=dict(parse_only=bs4.SoupStrainer(["article", "span", "div", "h1", "h2", "h3"])),
            )
            if (page_content := loader.load()) and len(page_content) > 0:
                splits: List[Document] = summarizer.text_splitter.split_documents(page_content)
                v_store = Chroma.from_documents(splits, lc_llm.create_embeddings())
                retriever = v_store.as_retriever()
                scrap_prompt = PromptTemplate(
                    input_variables=["context", "question"], template=prompt.read_prompt("qstring")
                )

                def format_docs(docs):
                    return "\n\n".join(doc.page_content for doc in docs)

                rag_chain = (
                    {"context": retriever | format_docs, "question": RunnablePassthrough()}
                    | scrap_prompt
                    | lc_llm.create_model()
                    | StrOutputParser()
                )

                output: Output = rag_chain.invoke(search.question)
                # cleanup
                v_store.delete_collection()
                log.info("Scrapping sites returned: '%s'", str(output))

                return self.refine_search(search.question, str(output), "", search.sites)
        return msg.no_output("search")

    def refine_search(self, question: str, result: str, terms: str, sites: list[str]) -> str:
        """Refines the text retrieved by the search engine.
        :param question: The user question, used to refine the context.
        :param result: The search result to refine.
        :param terms: The terms used on the Google search.
        :param sites: The list of source sites used on the search.
        """
        refine_prompt = PromptTemplate.from_template(self.refine_template()).format(
            idiom=shared.idiom,
            sources=sites,
            location=geo_location.location,
            datetime=geo_location.datetime,
            result=result,
            question=question,
        )
        log.info("STT::[QUESTION] '%s'", result)
        llm = lc_llm.create_chat_model(temperature=Temperature.CREATIVE_WRITING.temp)

        if (response := llm.invoke(refine_prompt)) and (output := response.content):
            output = output
        else:
            output = "The search did not bring any result"

        return self.wrap_response(terms, output, sites)


assert (internet := InternetService().INSTANCE) is not None
