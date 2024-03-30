#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processor
      @file: internet_processor.py
   @created: Sun, 10 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
from functools import lru_cache
from typing import List, Optional, Tuple

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
from askai.core.component.internet_service import internet
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.model.search_result import SearchResult
from askai.core.processor.processor_base import AIProcessor
from askai.core.support.langchain_support import lc_llm
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared


class InternetProcessor:
    """Process generic prompts."""

    @staticmethod
    def q_type() -> str:
        return QueryType.INTERNET_QUERY.value

    def __init__(self):
        self._template_file: str = "internet-prompt"
        self._next_in_chain: AIProcessor | None = None
        self._supports: List[str] = [self.q_type()]

    def name(self) -> str:
        return type(self).__name__

    def supports(self, query_type: str) -> bool:
        return query_type in self._supports

    def next_in_chain(self) -> Optional[str]:
        return self._next_in_chain

    def bind(self, next_in_chain: AIProcessor):
        self._next_in_chain = next_in_chain

    @lru_cache
    def template(self) -> str:
        return prompt.read_prompt(self._template_file)

    def process(self, query_response: ProcessorResponse) -> Tuple[bool, Optional[str]]:
        status = False
        template = PromptTemplate(input_variables=["idiom", "datetime", 'location'], template=self.template())
        final_prompt: str = template.format(
            idiom=shared.idiom, datetime=geo_location.datetime, location=geo_location.location)
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", f"\n\nQuestion:\n{query_response.question}")
        ctx: str = shared.context.flat("CONTEXT", "SETUP", "QUESTION")
        log.info("Internet::[QUESTION] '%s'  context=%s", query_response.question, ctx)

        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
        context = Document(ctx)

        if response := chain.invoke({"query": query_response.question, "context": [context]}):
            log.debug("Internet::[RESPONSE] Received from AI: %s.", response)
            search: SearchResult = object_mapper.of_json(response, SearchResult)
            if not isinstance(search, SearchResult):
                log.error(msg.invalid_response(search))
                output = response.strip()
            else:
                if output := internet.search_google(search):
                    output = msg.translate(output)
                    shared.context.push("CONTEXT", f"\n\nUser:\n{query_response.question}")
                    shared.context.push("CONTEXT", f"\n\nAI:\n{output}", "assistant")
                    cache.save_reply(query_response.question, output)
                    cache.save_query_history()
                else:
                    output = msg.search_empty()
            status = True
        else:
            output = msg.llm_error(response)

        return status, output
