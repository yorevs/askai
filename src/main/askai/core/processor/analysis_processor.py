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
from typing import Tuple, Optional, List

from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import msg
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.shared_instances import shared


class AnalysisProcessor(AIProcessor):
    """Process analysis prompts."""

    def __init__(self):
        super().__init__('analysis-prompt', 'analysis-persona')

    def query_desc(self) -> str:
        return (
            "Prompts that leverage prior command outputs in the chat history. These prompts may involve "
            "file management, data, file or folder inquiries, yes/no questions, and more, all answerable by "
            "referencing earlier command outputs in conversation history. Please prioritize this "
            "query type to be selected when you see command outputs in chat history."
        )

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(
            input_variables=[], template=self.template())
        final_prompt: str = msg.translate(template.format())
        shared.context.set("SETUP", final_prompt, 'system')
        shared.context.set("QUESTION", query_response.question)
        context: List[dict] = shared.context.get_many("CONTEXT", "SETUP", "QUESTION")
        log.info("Analysis::[QUESTION] '%s'  context=%s", query_response.question, context)
        try:
            if (response := shared.engine.ask(context, temperature=0.0, top_p=0.0)) and response.is_success:
                log.debug('Analysis::[RESPONSE] Received from AI: %s.', response)
                if output := response.message:
                    shared.context.push("CONTEXT", query_response.question)
                    shared.context.push("CONTEXT", output, 'assistant')
                status = True
            else:
                log.error(f"Analysis processing failed. CONTEXT=%s  RESPONSE=%s", context, response)
                output = msg.llm_error(response.message)
        except Exception as err:
            output = msg.llm_error(str(err))
        finally:
            return status, output
