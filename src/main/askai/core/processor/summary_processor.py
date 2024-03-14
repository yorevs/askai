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
from typing import Tuple, Optional

from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.component.summarizer import summarizer
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.query_response import QueryResponse
from askai.core.model.summary_result import SummaryResult
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import DocumentsNotFound


class SummaryProcessor(AIProcessor):
    """Process generic prompts."""

    def __init__(self):
        super().__init__("summary-prompt", "summary-persona")

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(input_variables=['os_type'], template=self.template())
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
                    summarizer.generate(summary.folder, summary.glob)
                    if results := summarizer.query('Give me an overview of all the summarized content'):
                        summary.results = results
                        output = self._wrap_output(query_response, summary)
                        shared.context.set("CONTEXT", output, "assistant")
                        cache.save_reply(query_response.question, output)
                status = True
            else:
                output = msg.llm_error(response.message)
        except (FileNotFoundError, ValueError, DocumentsNotFound) as err:
            output = msg.llm_error(err)
            status = True

        return status, output

    def _wrap_output(self, query_response: QueryResponse, summary_result: SummaryResult) -> str:
        """Wrap the output into a new string to be forwarded to the next processor.
        :param query_response: The query response provided by the AI.
        :param summary_result: The summary results.
        """
        query_response.query_type = self.next_in_chain().query_type()
        query_response.require_summarization = False
        query_response.require_internet = False
        query_response.response = str(summary_result)
        return str(query_response)
