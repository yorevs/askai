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
from askai.core.component.summarizer import summarizer
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.ai_reply import AIReply
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
from textwrap import dedent
from typing import List, Literal

import bs4
import logging as log
import re


class InternetService(metaclass=Singleton):
    """Provide an internet search service to complete queries that require real-time data. This service allows for the
    retrieval of up-to-date information from the web, enabling queries that depend on current data.
    """

    INSTANCE: "InternetService"

    ASKAI_INTERNET_DATA_KEY = "askai-internet-data"

    @staticmethod
    def _build_google_query(search: SearchResult) -> str:
        """Build a Google Search query from the provided search parameters.
        :param search: The AI search parameters encapsulated in a SearchResult object.
        :return: A string representing the constructed Google Search query.
        """
        # The order of conditions is important here, as the execution may stop early if a condition is met.
        final_query = ""
        # Gather the sites to be used in the search.
        if search.sites:
            final_query += f" {' OR '.join(['site:' + url for url in search.sites])}"
        # Weather is a filter that does not require any other search parameters.
        if search.filters and any(f.find("weather:") >= 0 for f in search.filters):
            return final_query + " " + re.sub(r"^weather:(.*)", r'weather:"\1"', " AND ".join(search.filters))
        # We want to find pages containing the exact name of the person.
        if search.filters and any(f.find("people:") >= 0 for f in search.filters):
            return final_query + " " + f" intext:\"{'+'.join([f.split(':')[1] for f in search.filters])}\" "
        # Make the search query using the provided keywords.
        if search.keywords:
            final_query = f"{' '.join(search.keywords)} {final_query} "

        return final_query

    @staticmethod
    def _wrap_response(terms: str, output: str, sites: list[str], method: Literal["Google", "Other"] = "Google") -> str:
        """Format and wrap the search response based on the search terms, output, and method used.
        :param terms: The search terms used in the query.
        :param output: The raw output or results from the search.
        :param sites: A list of websites included in or relevant to the search results.
        :param method: The search method used, either 'Google' or 'Other'.
        :return: A formatted string that encapsulates the search response.
        """
        method_icon = {"google": "", "other": ""}
        return dedent(
            f"""
            Your {method.title()} search returned the following:
            {output}
            \n---\n
            Sources: {', '.join(sites)}
            *{method_icon[method]} Accessed: {geo_location.location} {now('%d %B, %Y')}*
            >  Terms: {terms}"""
        ).strip()

    def __init__(self):
        API_KEYS.ensure("GOOGLE_API_KEY", "google_search")
        self._google = GoogleSearchAPIWrapper(google_api_key=API_KEYS.GOOGLE_API_KEY)
        self._tool = Tool(name="google_search", description="Search Google for recent results.", func=self._google.run)
        self._text_splitter = RecursiveCharacterTextSplitter(
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
        events.reply.emit(reply=AIReply.info(msg.searching()))
        search.sites = search.sites or ["google.com", "bing.com", "duckduckgo.com", "ask.com"]
        terms = self._build_google_query(search).strip()
        try:
            log.info("Searching Google for '%s'", terms)
            events.reply.emit(reply=AIReply.debug(msg.final_query(terms)))
            ctx = str(self._tool.run(terms))
            llm_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
            context: List[Document] = [Document(ctx)]
            chain = create_stuff_documents_chain(
                lc_llm.create_chat_model(temperature=Temperature.CREATIVE_WRITING.temp), llm_prompt
            )
            output = chain.invoke({"query": search.question, "context": context})
        except HttpError as err:
            return msg.fail_to_search(str(err))

        return self.refine_search(search.question, output, terms, search.sites)

    def scrap_sites(self, search: SearchResult) -> str:
        """Scrape a web page and summarize its contents.
        :param search: The AI search parameters encapsulated in a SearchResult object.
        :return: A string containing the summarized contents of the scraped web page.
        """
        events.reply.emit(reply=AIReply.info(msg.scrapping()))
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

                def _format_docs(docs) -> str:
                    return "\n\n".join(doc.page_content for doc in docs)

                rag_chain = (
                    {"context": retriever | _format_docs, "question": RunnablePassthrough()}
                    | scrap_prompt
                    | lc_llm.create_model()
                    | StrOutputParser()
                )

                output: Output = rag_chain.invoke(search.question)
                v_store.delete_collection()  # cleanup
                log.info("Scrapping sites returned: '%s'", str(output))
                return self.refine_search(search.question, str(output), "", search.sites)
        return msg.no_output("search")

    def refine_search(self, question: str, result: str, terms: str, sites: list[str]) -> str:
        """Refine the text retrieved by the search engine.
        :param question: The user's question, used to refine and contextualize the search results.
        :param result: The raw search result text that needs refinement.
        :param terms: The search terms used in the Google search.
        :param sites: The list of source sites that were included in the search.
        :return: A refined version of the search result text, tailored to better answer the user's question.
        """
        refine_prompt = PromptTemplate.from_template(self.refine_template).format(
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
            return self._wrap_response(terms, output, sites)

        return msg.no_good_result()


assert (internet := InternetService().INSTANCE) is not None
