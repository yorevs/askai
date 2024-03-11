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
from typing import Tuple, Optional, List

from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import msg
from askai.core.component.cache_service import cache
from askai.core.component.summarizer import summarizer
from askai.core.model.query_response import QueryResponse
from askai.core.model.summary_result import SummaryResult
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared


class SummaryProcessor(AIProcessor):
    """Process generic prompts."""

    def __init__(self):
        super().__init__("summary-prompt", "summary-persona")

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(input_variables=[], template=self.template())
        final_prompt: str = msg.translate(template.format())
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", query_response.question)
        context: List[dict] = shared.context.get_many("SETUP", "QUESTION")
        log.info("Setup::[SUMMARY] '%s'  context=%s", query_response.question, context)
        try:
            if (response := shared.engine.ask(context, temperature=0.0, top_p=0.0)) and response.is_success:
                summary_result: SummaryResult = object_mapper.of_json(response.message, SummaryResult)
                if results := summarizer.generate(summary_result.paths):
                    summary_result.results = results
                    output = self._wrap_output(query_response, summary_result)
                    shared.context.set("CONTEXT", output, "assistant")
                    cache.save_reply(query_response.question, output)
                    status = True
            else:
                output = msg.llm_error(response.message)
        except Exception as err:
            output = msg.llm_error(str(err))

        return status, output

    def _wrap_output(self, query_response: QueryResponse, summary_result: SummaryResult) -> str:
        """Wrap the output into a new string to be forwarded to the next processor.
        :param query_response: The query response provided by the AI.
        :param summary_result: The summary results.
        """
        query_response.query_type = self.next_in_chain().query_type()
        query_response.require_summarization = False
        query_response.response = str(summary_result)
        return str(query_response)
