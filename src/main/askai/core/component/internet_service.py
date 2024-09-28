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

import logging as log
import re
from collections import defaultdict
from typing import List

import bs4
import openai
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
        "paypal.com": "",
        "wikipedia.org": "荒",
        "reddit.com": "",
        "tiktok.com": "懲",
        "ubuntu.com": "",
        "fedora.com": "",
    })
    # fmt: on

    @classmethod
    def wrap_response(cls, terms: str, output: str, result: SearchResult) -> str:
        """Format and wrap the search response based on the search terms, output, and method used.
        :param terms: The search terms used in the query.
        :param output: The raw output or results from the search.
        :param result: The search result.
        :return: A formatted string that encapsulates the search response.
        """
        terms: str = re.sub(r"\s{2,}", " ", terms)
        sites: set[str] = set(re.findall(r"site:(.+?\..+?)\s+", terms) + result.sites)
        sources: str = " ".join(
            filter(len, set(sorted([f"{s.replace(s, cls.SITE_ICONS[s]):<2}".strip() or s for s in sites], key=len)))
        )
        # fmt: off
        return (
            f"Your {result.engine.title()} search has returned the following results:"
            f"\n\n{output}\n\n---\n\n"
            f"`{cls.CATEGORY_ICONS[result.category]:<2} {result.category}`  **Sources:** {sources}  "
            f"**Access:** {geo_location.location} - *{now('%B %d, %Y')}*\n\n"
            f">   Terms: {terms}")
        # fmt: on

    @staticmethod
    def _build_google_query(search: SearchResult) -> str:
        """Build a Google Search query from the provided search parameters.
        :param search: The AI search parameters encapsulated in a SearchResult object.
        :return: A string representing the constructed Google Search query.
        """
        # The order of conditions is important here, as the execution may stop early if a condition is met.
        google_query = ""
        match search.category.casefold():
            case "people":
                if any((f.find("intext:") >= 0 for f in search.filters)):
                    google_query = (
                        "description AND background AND work AND achievements "
                        f'{next((f for f in search.filters if f.startswith("intext:")), None)}'
                    )
            case "weather":
                if any((f.find("weather:") >= 0 for f in search.filters)):
                    google_query = (
                        f'{now("%B %d %Y")} {next((f for f in search.filters if f.startswith("weather:")), None)}'
                    )
            case _:
                if search.keywords:
                    # Gather the sites to be used in the search.
                    sites = f"{' OR '.join(set('site:' + url for url in search.sites))}"
                    google_query = f"{' '.join(set(sorted(search.keywords)))} {sites}"

        return google_query

    def __init__(self):
        API_KEYS.ensure("GOOGLE_API_KEY", "google_search")
        self._google = GoogleSearchAPIWrapper(k=10, google_api_key=API_KEYS.GOOGLE_API_KEY)
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
        terms: str = self._build_google_query(search).strip()
        question: str = re.sub(r"(\w+:)*|((\w+\.\w+)*)", "", terms, flags=re.DOTALL | re.MULTILINE)
        try:
            log.info("Searching Google for '%s'", terms)
            events.reply.emit(reply=AIReply.debug(msg.final_query(terms)))
            results: list[str] = str(self._tool.run(terms, verbose=configs.is_debug)).split(" ")
            llm_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "Use the following context to answer the question at the end:\\n\\n{context}"),
                    ("human", "{question}"),
                ]
            )
            docs: List[Document] = [Document(d) for d in results]
            chain = create_stuff_documents_chain(
                lc_llm.create_chat_model(temperature=Temperature.COLDEST.temp), llm_prompt
            )
            output = chain.invoke({"question": question, "context": docs})
        except (HttpError, openai.APIError) as err:
            return msg.fail_to_search(str(err))

        return self.refine_search(terms, output, search)

    def refine_search(self, terms: str, response: str, search: SearchResult) -> str:
        """Refine the text retrieved by the search engine.
        :param terms: The search terms used in the search.
        :param response: The internet search response.
        :param search: The search result object.
        :return: A refined version of the search result text, tailored to better answer the user's question.
        """
        refine_prompt = PromptTemplate.from_template(self.refine_template).format(
            idiom=shared.idiom,
            sources=search.sites,
            location=geo_location.location,
            datetime=geo_location.datetime,
            result=response,
            question=search.question,
        )
        log.info("STT::[QUESTION] '%s'", response)
        llm = lc_llm.create_chat_model(temperature=Temperature.CREATIVE_WRITING.temp)

        if (response := llm.invoke(refine_prompt)) and (output := response.content):
            return self.wrap_response(terms, output, search)

        return msg.no_good_result()

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
                return self.refine_search(search.question, str(output), search)
        return msg.no_output("search")


assert (internet := InternetService().INSTANCE) is not None
