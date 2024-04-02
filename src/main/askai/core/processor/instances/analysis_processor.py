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
from typing import List, Optional, Tuple

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.processor.processor_base import AIProcessor
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


class AnalysisProcessor:
    """Process analysis prompts."""

    @staticmethod
    def q_type() -> str:
        return QueryType.ANALYSIS_QUERY.value

    def __init__(self):
        self._template_file: str = "analysis-prompt"
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
        template = PromptTemplate(
            input_variables=['idiom', 'question'], template=self.template())
        final_prompt: str = template.format(idiom=shared.idiom, question=query_response.question)
        ctx: str = shared.context.flat("CONTEXT")
        log.info("Analysis::[QUESTION] '%s'  context=%s", final_prompt, ctx)

        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
        context = [Document(ctx)]

        if response := chain.invoke({"query": final_prompt, "context": context}):
            log.debug("Analysis::[RESPONSE] Received from AI: %s.", response)
            if response and shared.UNCERTAIN_ID not in response:
                shared.context.push("CONTEXT", f"\n\nUser:\n{query_response.question}")
                shared.context.push("CONTEXT", f"\n\nAI:\n{response}", "assistant")
            else:
                response = msg.translate("I don't know.")
            status = True
        else:
            log.error(f"Analysis processing failed. CONTEXT=%s  RESPONSE=%s", context, response)
            response = msg.llm_error(response)

        return status, response
