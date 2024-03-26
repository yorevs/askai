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
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.processor.processor_base import AIProcessor
from askai.core.support.shared_instances import shared


class GenericProcessor:
    """Process generic prompts."""

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
        template = PromptTemplate(input_variables=["user"], template=self.template())
        final_prompt: str = msg.translate(template.format(user=prompt.user))
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", query_response.question)
        context: ContextRaw = shared.context.join("GENERAL", "SETUP", "QUESTION")
        log.info("Setup::[GENERIC] '%s'  context=%s", query_response.question, context)

        if (response := shared.engine.ask(context, *Temperatures.CREATIVE_WRITING.value)) and response.is_success:
            output = response.message
            shared.context.push("GENERAL", output, "assistant")
            cache.save_reply(query_response.question, output)
            cache.save_query_history()
            status = True
        else:
            output = msg.llm_error(response.message)

        return status, output
