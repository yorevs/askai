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
import os
from functools import lru_cache
from typing import List, Optional, Tuple

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.summarizer import summarizer
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.model.summary_result import SummaryResult
from askai.core.processor.processor_base import AIProcessor
from askai.core.support.langchain_support import lc_llm
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from askai.exception.exceptions import DocumentsNotFound


class SummaryProcessor:
    """Process generic prompts."""

    @staticmethod
    def _ask_and_reply(question: str) -> Optional[str]:
        """Query the summarized for questions related to the summarized content.
        :param question: the question to be asked to the AI.
        """
        output = None
        if results := summarizer.query(question):
            output = os.linesep.join([r.answer for r in results]).strip()
        return output

    @staticmethod
    def q_type() -> str:
        return QueryType.SUMMARY_QUERY.value

    def __init__(self):
        self._template_file: str = "summary-prompt"
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
            input_variables=['os_type', 'idiom', 'question'], template=self.template())
        final_prompt: str = template.format(
            os_type=prompt.os_type, idiom=shared.idiomm,
            question=query_response.question)
        ctx: str = shared.context.flat("CONTEXT")
        log.info("Summary::[QUESTION] '%s'  context=%s", final_prompt, ctx)

        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
        context = [Document(ctx)]

        try:
            if response := chain.invoke({"query": query_response.question, "context": context}):
                log.debug("Summary::[RESPONSE] Received from AI: %s.", response)
                summary: SummaryResult = object_mapper.of_json(response, SummaryResult)
                if not isinstance(summary, SummaryResult):
                    log.error(msg.invalid_response(SummaryResult))
                    output = response
                else:
                    if not summarizer.exists(summary.folder, summary.glob):
                        if not summarizer.generate(summary.folder, summary.glob):
                            return True, msg.summary_not_possible()
                    else:
                        summarizer.folder = summary.folder
                        summarizer.glob = summary.glob
                        log.info("Reusing persisted summarized content: '%s'/'%s'", summary.folder, summary.glob)
                    output = self._qna()
                status = True
            else:
                output = msg.llm_error(response)
        except (FileNotFoundError, ValueError, DocumentsNotFound) as err:
            output = msg.llm_error(err)
            status = True

        return status, output

    def _qna(self) -> str:
        """Questions and Answers about the summarized content."""
        display_text(
            f"# {msg.enter_qna()} %EOL%"
            f"> Content:  {summarizer.sum_path} %EOL%%EOL%"
            f"`{msg.press_esc_enter()}` %EOL%"
        )
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.qna_welcome())
        while question := shared.input_text(f"{shared.username}: %GREEN%"):
            if not (output := self._ask_and_reply(question)):
                break
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"%GREEN%{output}%NC%")
        display_text(f"# {msg.leave_qna()} %EOL%")

        return msg.welcome_back()
