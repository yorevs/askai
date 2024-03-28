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
from typing import Optional, Tuple, List

from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
from askai.core.component.internet_service import internet
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.model.search_result import SearchResult
from askai.core.processor.processor_base import AIProcessor
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
        template = PromptTemplate(input_variables=['idiom', 'datetime'], template=self.template())
        final_prompt: str = template.format(idiom=shared.idiom, datetime=geo_location.now)
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", f"\n\nQuestion: {query_response.question}\n\nHelpful Answer:")
        context: ContextRaw = shared.context.join("SETUP", "QUESTION")
        log.info("Setup::[INTERNET] '%s'  context=%s", query_response.question, context)

        if not (response := cache.read_reply(query_response.question)):
            if (response := shared.engine.ask(context, *Temperatures.CHATBOT_RESPONSES.value)) and response.is_success:
                search: SearchResult = object_mapper.of_json(response.message, SearchResult)
                if not isinstance(search, SearchResult):
                    log.error(msg.invalid_response(search))
                    output = response.message.strip()
                else:
                    if output := internet.search_google(search):
                        output = msg.translate(output)
                        shared.context.push("GENERAL", query_response.question)
                        shared.context.push("GENERAL", output, "assistant")
                        cache.save_reply(query_response.question, output)
                        cache.save_query_history()
                    else:
                        output = msg.search_empty()
                status = True
            else:
                output = msg.llm_error(response.message)
        else:
            log.debug('Reply found for "%s" in cache.', query_response.question)
            output = response
            shared.context.set("CONTEXT", output, "assistant")
            status = True

        return status, output
