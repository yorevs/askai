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
from typing import Optional, Tuple

from langchain_core.prompts import PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.summarizer import summarizer
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.query_response import QueryResponse
from askai.core.model.summary_result import SummaryResult
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from askai.exception.exceptions import DocumentsNotFound


class SummaryProcessor(AIProcessor):
    """Process generic prompts."""

    def __init__(self):
        super().__init__("summary-prompt", "summary-persona")

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(input_variables=["os_type"], template=self.template())
        final_prompt: str = msg.translate(template.format(os_type=prompt.os_type))
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
                        summarizer.generate(summary.folder, summary.glob)
                    else:
                        log.info("Reusing persisted summarized content: '%s'/'%s'", summary.folder, summary.glob)
                    output = self.qna()
                status = True
            else:
                output = msg.llm_error(response.message)
        except (FileNotFoundError, ValueError, DocumentsNotFound) as err:
            output = msg.llm_error(err)
            status = True

        return status, output

    @staticmethod
    def _ask_and_reply(question: str) -> Optional[str]:
        """TODO"""
        output = None
        if results := summarizer.query(question):
            output = os.linesep.join([r.answer for r in results]).strip()
            shared.context.push("SUMMARY", question)
            shared.context.push("SUMMARY", output, "assistant")
        return output

    def qna(self) -> str:
        """TODO"""
        display_text(
            f"%ORANGE%{'-=' * 40}%EOL%"
            f"{msg.enter_qna()}%EOL%"
            f"{'-=' * 40}%NC%"
        )
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.qna_welcome())
        while question := shared.input_text(f"{shared.username}: %CYAN%"):
            if not (output := self._ask_and_reply(question)):
                break
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"%CYAN%{output}%NC%")
        display_text(
            f"%ORANGE%{'-=' * 40}%EOL%"
            f"{msg.leave_qna()}%EOL%"
            f"{'-=' * 40}%NC%"
        )
        return msg.welcome_back()
