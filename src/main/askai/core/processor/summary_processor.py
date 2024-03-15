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
from langchain_core.prompts import PromptTemplate
from typing import Optional, Tuple

import logging as log
import os


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
                    if not summarizer.exists(summary.folder, summary.glob):
                        summarizer.generate(summary.folder, summary.glob)
                        if results := summarizer.query("Give me an overview of all the summarized content"):
                            output = os.linesep.join([r.answer for r in results]).strip()
                            shared.context.set("CONTEXT", output, "assistant")
                            cache.save_reply(query_response.question, output)
                        else:
                            log.info("Reusing existing summary: '%s'/'%s'", summary.folder, summary.glob)
                status = True
            else:
                output = msg.llm_error(response.message)
        except (FileNotFoundError, ValueError, DocumentsNotFound) as err:
            output = msg.llm_error(err)
            status = True

        return status, output
