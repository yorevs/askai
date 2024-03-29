#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processor
      @file: analysis_processor.py
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
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.processor.processor_base import AIProcessor
from askai.core.support.shared_instances import shared


class AnalysisProcessor:
    """Process analysis prompts."""

    @staticmethod
    def _wrap_output(query_response: ProcessorResponse) -> str:
        """Wrap the output into a new string to be forwarded to the next processor.
        :param query_response: The query response provided by the AI.
        """
        query_response.query_type = QueryType.GENERIC_QUERY.value
        query_response.require_summarization = False
        query_response.forwarded = True
        query_response.commands.clear()

        return str(query_response)

    @staticmethod
    def q_type() -> str:
        return QueryType.ANALYSIS_QUERY.value

    def __init__(self):
        self._template_file: str = "analysis-prompt"
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
        template = PromptTemplate(input_variables=['idiom'], template=self.template())
        final_prompt: str = template.format(idiom=shared.idiom)
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", query_response.question)
        context: ContextRaw = shared.context.join("CONTEXT", "SETUP", "QUESTION")
        log.info("Analysis::[QUESTION] '%s'  context=%s", query_response.question, context)

        if (response := shared.engine.ask(context, *Temperatures.CODE_GENERATION.value)) and response.is_success:
            log.debug("Analysis::[RESPONSE] Received from AI: %s.", response)
            if response.message and shared.UNCERTAIN_ID != (output := response.message):
                shared.context.push("CONTEXT", query_response.question)
                shared.context.push("CONTEXT", output, "assistant")
            else:
                self._next_in_chain = QueryType.GENERIC_QUERY.proc_name
                output = self._wrap_output(query_response)
            status = True
        else:
            log.error(f"Analysis processing failed. CONTEXT=%s  RESPONSE=%s", context, response)
            output = msg.llm_error(response.message)

        return status, output
