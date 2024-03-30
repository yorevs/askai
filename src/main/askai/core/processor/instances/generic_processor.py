#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processor
      @file: generic_processor.py
   @created: Fri, 23 Feb 2024
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
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.processor.processor_base import AIProcessor
from askai.core.support.shared_instances import shared


class GenericProcessor:
    """Process generic prompts."""

    @staticmethod
    def _wrap_output(query_response: ProcessorResponse) -> str:
        """Wrap the output into a new string to be forwarded to the next processor.
        :param query_response: The query response provided by the AI.
        """
        query_response.query_type = QueryType.INTERNET_QUERY.value
        query_response.require_summarization = False
        query_response.forwarded = True
        query_response.commands.clear()

        return str(query_response)

    @staticmethod
    def q_type() -> str:
        return QueryType.GENERIC_QUERY.value

    def __init__(self):
        self._template_file: str = "generic-prompt"
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
        template = PromptTemplate(input_variables=['user', 'datetime', 'idiom'], template=self.template())
        final_prompt: str = template.format(user=prompt.user, datetime=geo_location.now, idiom=shared.idiom)
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", f"\n\nQuestion:\n{query_response.question}")
        context: ContextRaw = shared.context.join("GENERAL", "SETUP", "QUESTION")
        log.info("Setup::[GENERIC] '%s'  context=%s", query_response.question, context)

        if (response := shared.engine.ask(context, *Temperatures.CREATIVE_WRITING.value)) and response.is_success:
            log.debug("General::[RESPONSE] Received from AI: %s.", response)
            if response.message and shared.INTERNET_ID != (output := response.message):
                shared.context.push("GENERAL", f"\n\nUser:\n{query_response.question}")
                shared.context.push("GENERAL", f"\n\nAI:\n{output}", "assistant")
                cache.save_reply(query_response.question, output)
                cache.save_query_history()
            else:
                self._next_in_chain = QueryType.GENERIC_QUERY.proc_name
                output = self._wrap_output(query_response)
            status = True
        else:
            log.error(f"General processing failed. CONTEXT=%s  RESPONSE=%s", context, response)
            output = msg.llm_error(response.message)

        return status, output
