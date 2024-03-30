#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processor
      @file: output_processor.py
   @created: Fri, 23 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
from functools import lru_cache
from typing import Optional, Tuple, List

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.processor.processor_base import AIProcessor
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


class OutputProcessor(AIProcessor):
    """Process command output prompts."""

    @staticmethod
    def q_type() -> str:
        return QueryType.OUTPUT_QUERY.value

    def __init__(self):
        self._template_file: str = "output-prompt"
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
        commands = "; ".join([c.cmd_line for c in query_response.commands])
        template = PromptTemplate(input_variables=['command_line', 'shell', 'idiom'], template=self.template())
        final_prompt: str = template.format(command_line=commands, shell=prompt.shell, idiom=shared.idiom)
        shared.context.set("SETUP", final_prompt, "system")
        ctx: str = shared.context.flat("CONTEXT", "SETUP", "QUESTION")
        log.info("Output::[QUESTION] '%s'  context=%s", query_response.question, ctx)

        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
        context = Document(ctx)

        if response := chain.invoke({"query": query_response.question, "context": [context]}):
            log.debug("Output::[RESPONSE] Received from AI: %s.", response)
            if output := response:
                shared.context.push("CONTEXT", f"\n\nAI:\n{output}", "assistant")
            status = True
        else:
            log.error(f"Output processing failed. CONTEXT=%s  RESPONSE=%s", context, response)
            output = msg.llm_error(response)

        return status, output
