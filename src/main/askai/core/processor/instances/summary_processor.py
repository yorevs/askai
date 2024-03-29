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
from typing import Optional, Tuple, List

from langchain_core.prompts import PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.summarizer import summarizer
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.model.summary_result import SummaryResult
from askai.core.processor.processor_base import AIProcessor
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
        template = PromptTemplate(input_variables=['os_type', 'idiom'], template=self.template())
        final_prompt: str = template.format(os_type=prompt.os_type, idiom=shared.idiom)
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", query_response.question)
        context: ContextRaw = shared.context.join("SETUP", "QUESTION")
        log.info("Setup::[SUMMARY] '%s'  context=%s", query_response.question, context)

        try:
            if (response := shared.engine.ask(context, *Temperatures.CHATBOT_RESPONSES.value)) and response.is_success:
                summary: SummaryResult = object_mapper.of_json(response.message, SummaryResult)
                if not isinstance(summary, SummaryResult):
                    log.error(msg.invalid_response(SummaryResult))
                    output = response.message
                else:
                    shared.context.clear("SUMMARY")
                    if not summarizer.exists(summary.folder, summary.glob):
                        if not summarizer.generate(summary.folder, summary.glob):
                            return True, "%ORANGE%Sorry, summarization was not possible !%NC%"
                    else:
                        summarizer.folder = summary.folder
                        summarizer.glob = summary.glob
                        log.info("Reusing persisted summarized content: '%s'/'%s'", summary.folder, summary.glob)
                    output = self._qna()
                status = True
            else:
                output = msg.llm_error(response.message)
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
